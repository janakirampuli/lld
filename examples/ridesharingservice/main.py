'''

requirements:
1. passenger requests ride: pickup, destination, ride type
2. system matches nearest available driver
3. driver accepts/declines
4. fare calculated based on distance, time, ride type
5. real time tracking during ride
6. payment processed on ride completion
7. concurrent ride requests -> thread-safe matching
8. no double assignment of a driver

core entities:
User
Passenger
Driver
Ride
RideRequest
Location
Vehicle
Payment
Rating

enums:
RideType: REGULAR, PREMIUM, XL
RideStatus: REQUESTED, MATCHED, ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED
DriverStatus: AVAILABLE, BUSY, OFFLINE
PaymentStatus: PENDING, SUCCESS, FAILED, REFUNDED
VehicleType: SEDAN, SUV, LUXURY

classes and interfaces:

DriverMatchingStrategy()
- match(request, drivers)

FareCalculator()
- calculate(distance_km, duration_min, ride_type)

PaymentProcessor()
- process_payment(amount, method)
- process_refund(payment_id, amount)

NotificationService()
- notify(user_id, message)

LocationTracker()
- get_current_location(driver_id)
- update_location(driver_id, location)

Location:
- latitude
- longitude

User:
- user_id
- name
- email
- phone

Passenger(User):
- ride_history
- current_ride
- payment_method

Driver(User):
- license_number
- vehicle
- status
- current_location
- rating
- current_ride
- ride_history

Vehicle:
- vehicle_id
- license_plate
- vehicle_type

RideRequest:
- request_id
- passenger
- pickup
- destination
- ride_type
- request_time

Ride:
- ride_id
- request
- driver
- passenger
- pickup
- destination
- status
- start_time
- end_time
- distance_km
- duration_min
- fare
- payment

Payment:
- payment_id
- ride_id
- amount
- method
- status

Rating:
- rating_id
- ride_id
- rated_by
- rated_for
- score
- comment

RideSharingSystem:
- drivers
- passengers
- active_riders
- matching_strategy
- fare_calculator
- payment_processor
- notification_service
- location_tracker
- request_queue

RideService:
- request_ride(passenger, pickup, destination, ride_type)
- accept_ride(driver_id, ride_id)
- decline_ride(driver_id, ride_id)
- start_ride(ride_id)
- complete_ride(ride_id)
- cancel_ride(ride_id, cancelled_by)
- rate_ride(ride_id, rated_by, score, comment)

DriverService:
- register_driver(driver)
- update_location(driver_id, location)
- set_availability(driver_id, status)
- get_avialable_drivers(ride_type)

NearestDriverStrategy(DriverMatchingStrategy):
- match(request, deivers) -> Driver
    filter by status, vehicle type matches ride type
    sort by distance
    return closest

StandardFareCalculator(FareCalculator):
- base_fare
- per_km_rate
- per_min_rate
- calculate(distance_km, duration_min, ride_type)
    base + per_km * distance_km + per_min_rate * duration_min

concurrency handling:
match_and_assign(request):
    available = driver_service.get_avialable_drivers(request.ride_type)
    driver = matching_strategy.match(request, available)
    if driver is None: return None

    with _driver_locks[driver.driver_id]:
        if driver.status != AVAILABLE:
            return match_and_assign(request)
        driver.status = BUSY
        driver.current_ride = ride
    
    notify driver
    notify ride


'''

from enum import Enum
import uuid
import threading
import time
from typing import Dict

class RideStatus(Enum):
    REQUESTED = 1
    ACCEPTED = 2
    IN_PROGRESS = 3
    COMPLETED = 4
    CANCELLED = 5

class RideType(Enum):
    REGULAR = 1
    PREMIUM = 2

class Location:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
    
    def distance_to(self, other):
        return ((self.lat - other.lat)**2 + (self.lon - other.lon)**2)**0.5

class User:
    def __init__(self, name, contact):
        self.id = str(uuid.uuid4())
        self.name = name
        self.contact = contact

class Driver(User):
    def __init__(self, name, contact, vehicle_no):
        super().__init__(name, contact)
        self.vehicle_no = vehicle_no
        self.is_available = True
        self.current_location = None

    def set_avialability(self, available):
        self.is_available = available

class Passenger(User):
    def __init__(self, name, contact):
        super().__init__(name, contact)

class Ride:
    def __init__(self, passenger: Passenger, driver: Driver, src: Location, dest: Location, ride_type: RideType):
        self.id = str(uuid.uuid4())
        self.passenger = passenger
        self.driver = driver
        self.src = src
        self.dest = dest
        self.ride_type = ride_type
        self.status = RideStatus.REQUESTED
        self.fare = 0.0
        self.start_time = None
        self.end_time = None


class RideService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RideService, cls).__new__(cls)
                    cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        self.drivers: Dict[str, Driver] = {}
        self.passengers: Dict[str, Passenger] = {}
        self.rides: Dict[str, Ride] = {}
        self.mathcing_lock = threading.Lock()

    def add_passenger(self, passenger: Passenger):
        self.passengers[passenger.id] = passenger

    def add_driver(self, driver: Driver, location: Location):
        driver.current_location = location
        self.drivers[driver.id] = driver
    

    def find_nearest_driver(self, src) -> Driver:
        nearest_driver = None
        min_dist = float("inf")

        for driver in self.drivers.values():
            if driver.is_available:
                dist = driver.current_location.distance_to(src)
                if dist < min_dist:
                    min_dist = dist
                    nearest_driver = driver

        return nearest_driver
    
    def request_ride(self, passenger: Passenger, src: Location, dest: Location, ride_type: RideType):
        

        with self.mathcing_lock:
            selected_driver = self.find_nearest_driver(src)

            if not selected_driver:
                print("No drivers available")
                return None
            
            ride = Ride(passenger, selected_driver, src, dest, ride_type)
            ride.status = RideStatus.ACCEPTED

            selected_driver.is_available = False
            self.rides[ride.id] = ride
            print(f"--- RIDE BOOKED ---")
            print(f"Ride ID: {ride.id}")
            print(f"Passenger: {passenger.name}")
            print(f"Driver: {selected_driver.name} ({selected_driver.vehicle_no})")
            print(f"From: {src.lat, src.lon} To: {dest.lat, dest.lon}")

            return ride
        
    def calculate_fare(self, ride: Ride):
        rate_per_km = 1.0
        return ride.src.distance_to(ride.dest) * rate_per_km
    
    def start_ride(self, ride: Ride):
        ride.status = RideStatus.IN_PROGRESS
        ride.start_time = time.time()
        print("Ride started...")

    def complete_ride(self, ride: Ride):
        ride.status = RideStatus.COMPLETED
        ride.end_time = time.time()
        ride.driver.current_location = ride.dest
        ride.driver.is_available = True

        ride.fare = self.calculate_fare(ride)
        print(f"ride completed fare: {ride.fare}")

def demo():
    service = RideService()

    p1 = Passenger("A", "123")
    p2 = Passenger("B", "456")

    service.add_passenger(p1)
    service.add_passenger(p2)

    d1 = Driver("C", "789", "AP123")
    d2 = Driver("D", "234", "KA456")

    service.add_driver(d1, Location(1, 1))
    service.add_driver(d2, Location(5, 5))

    a_loc = Location(2, 2)
    a_dest = Location(10, 10)

    ride1 = service.request_ride(p1, a_loc, a_dest, RideType.REGULAR)
    
    service.start_ride(ride1)
    # service.complete_ride(ride1)

    ride2 = service.request_ride(p2, Location(4,4), Location(1, 1), RideType.REGULAR)

    service.start_ride(ride2)

    ride3 = service.request_ride(p1, Location(0, 0), Location(1, 1), RideType.REGULAR)

    service.complete_ride(ride1)
    service.complete_ride(ride2)

if __name__ == "__main__":
    demo()