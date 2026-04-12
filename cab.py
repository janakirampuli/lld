from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional
import uuid
import math

# --- Enums ---

class CabStatus(Enum):
    AVAILABLE = "AVAILABLE"
    ON_TRIP = "ON_TRIP"

class TripStatus(Enum):
    REQUESTED = "REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

# --- Core Models ---

class Location:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: 'Location') -> float:
        # Simple Euclidean distance
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

class Rider:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name

class Cab:
    def __init__(self, plate_number: str):
        self.id = str(uuid.uuid4())
        self.plate_number = plate_number
        self.status = CabStatus.AVAILABLE
        self.current_location: Optional[Location] = None

class Driver:
    def __init__(self, name: str, cab: Cab):
        self.id = str(uuid.uuid4())
        self.name = name
        self.cab = cab

class Trip:
    def __init__(self, rider: Rider, cab: Cab, from_loc: Location, to_loc: Location, price: float):
        self.id = str(uuid.uuid4())
        self.rider = rider
        self.cab = cab
        self.from_loc = from_loc
        self.to_loc = to_loc
        self.price = price
        self.status = TripStatus.REQUESTED

    def start_trip(self):
        self.status = TripStatus.IN_PROGRESS
        self.cab.status = CabStatus.ON_TRIP

    def end_trip(self):
        self.status = TripStatus.COMPLETED
        self.cab.status = CabStatus.AVAILABLE
        self.cab.current_location = self.to_loc # Update cab's location to the drop-off point

# --- Strategy Patterns (The core of the LLD) ---

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, from_loc: Location, to_loc: Location) -> float:
        pass

class DefaultPricingStrategy(PricingStrategy):
    def __init__(self, rate_per_km: float = 10.0):
        self.rate_per_km = rate_per_km

    def calculate_price(self, from_loc: Location, to_loc: Location) -> float:
        distance = from_loc.distance_to(to_loc)
        return distance * self.rate_per_km

class CabMatchingStrategy(ABC):
    @abstractmethod
    def match_cab(self, rider: Rider, from_loc: Location, to_loc: Location, candidate_cabs: List[Cab]) -> Optional[Cab]:
        pass

class NearestCabMatchingStrategy(CabMatchingStrategy):
    def match_cab(self, rider: Rider, from_loc: Location, to_loc: Location, candidate_cabs: List[Cab]) -> Optional[Cab]:
        available_cabs = [cab for cab in candidate_cabs if cab.status == CabStatus.AVAILABLE and cab.current_location]
        if not available_cabs:
            return None
        
        # Sort by closest distance to rider
        available_cabs.sort(key=lambda cab: cab.current_location.distance_to(from_loc))
        return available_cabs[0]

# --- Managers ---

class CabManager:
    def __init__(self):
        self.cabs: Dict[str, Cab] = {}

    def register_cab(self, cab: Cab):
        self.cabs[cab.id] = cab

    def update_cab_location(self, cab_id: str, location: Location):
        if cab_id in self.cabs:
            self.cabs[cab_id].current_location = location

    def get_all_cabs(self) -> List[Cab]:
        return list(self.cabs.values())

# --- System Facade / Entry Point ---

class CabBookingSystem:
    def __init__(self, cab_manager: CabManager, pricing_strategy: PricingStrategy, matching_strategy: CabMatchingStrategy):
        self.cab_manager = cab_manager
        self.pricing_strategy = pricing_strategy
        self.matching_strategy = matching_strategy
        self.trips: Dict[str, Trip] = {}

    def book_trip(self, rider: Rider, from_loc: Location, to_loc: Location) -> Trip:
        # 1. Match a Cab
        all_cabs = self.cab_manager.get_all_cabs()
        matched_cab = self.matching_strategy.match_cab(rider, from_loc, to_loc, all_cabs)
        
        if not matched_cab:
            raise Exception("No cabs available nearby. Please try again later.")

        # 2. Calculate Price
        price = self.pricing_strategy.calculate_price(from_loc, to_loc)

        # 3. Create Trip
        trip = Trip(rider, matched_cab, from_loc, to_loc, price)
        self.trips[trip.id] = trip
        
        print(f"Trip booked successfully for {rider.name}. Cab: {matched_cab.plate_number}, Estimated Price: ${price:.2f}")
        return trip

# --- Demo / Driver Code ---

def demo():
    # 1. Setup the system
    cab_manager = CabManager()
    pricing_strategy = DefaultPricingStrategy(rate_per_km=15.0)
    matching_strategy = NearestCabMatchingStrategy()
    
    system = CabBookingSystem(cab_manager, pricing_strategy, matching_strategy)

    # 2. Register Cabs & Drivers
    cab1 = Cab("KA-01-1234")
    cab2 = Cab("MH-02-9876")
    
    cab_manager.register_cab(cab1)
    cab_manager.register_cab(cab2)

    # Update their locations
    cab_manager.update_cab_location(cab1.id, Location(0, 0))
    cab_manager.update_cab_location(cab2.id, Location(10, 10))

    # 3. Create a Rider
    rider = Rider("Alice")
    pickup_loc = Location(1, 1) # Closer to cab1
    dropoff_loc = Location(5, 5)

    # 4. Book a Trip
    try:
        trip = system.book_trip(rider, pickup_loc, dropoff_loc)
        
        # 5. Simulate Trip execution
        trip.start_trip()
        print(f"Trip {trip.id} status: {trip.status.value}")
        
        trip.end_trip()
        print(f"Trip {trip.id} status: {trip.status.value}. Cab is now at ({trip.cab.current_location.x}, {trip.cab.current_location.y})")
        
    except Exception as e:
        print(f"Booking failed: {e}")

if __name__ == "__main__":
    demo()