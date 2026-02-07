from enum import Enum
from abc import ABC
from typing import Optional, List
import threading
import random
import time

class VehicleType(Enum):
    CAR = 1
    TRUCK = 2

class Vehicle(ABC):
    def __init__(self, name: str, vehicle_type: VehicleType):
        self.name = name
        self.vehicle_type = vehicle_type

class Car(Vehicle):
    def __init__(self, name: str):
        super().__init__(name, VehicleType.CAR)
    
class Truck(Vehicle):
    def __init__(self, name):
        super().__init__(name, VehicleType.TRUCK)

class ParkingSpot:
    def __init__(self, spot_id: str, spot_type: VehicleType):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.parked_vehicle: Optional[Vehicle] = None

    def is_free(self):
        return self.parked_vehicle is None
    
    def park(self, vehicle: Vehicle):
        if (self.is_free() and self.spot_type == vehicle.vehicle_type):
            self.parked_vehicle = vehicle
            return True
        return False
    
    def unpark(self):
        self.parked_vehicle = None
        return True
    

class Level:
    def __init__(self, level_number: int, num_spots: int):
        self.level_number = level_number
        self.spots: List[ParkingSpot] = []
        self.level_lock = threading.Lock()

        for i in range(1, num_spots+1):
            spot_id = f"L_{level_number}-{i}"
            vehicle_type = VehicleType.CAR if random.randint(0, 1) == 1 else VehicleType.TRUCK
            self.spots.append(ParkingSpot(spot_id, vehicle_type))
        
    def park_vehicle(self, vehicle: Vehicle):
        with self.level_lock:
            for spot in self.spots:
                if (spot.is_free() and spot.spot_type == vehicle.vehicle_type):
                    spot.park(vehicle)
                    return spot
        return None
    
    def unpark_vehicle(self, vehicle: Vehicle):
        with self.level_lock:
            for spot in self.spots:
                if spot.parked_vehicle == vehicle:
                    spot.unpark()
                    return True
        return False
    
    def get_availability(self):
        stats = {"TRUCK": 0, "CAR": 0}
        for spot in self.spots:
            if spot.is_free():
                stats[spot.spot_type.name] += 1
        return stats
    
class ParkingLot:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ParkingLot, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.levels: List[Level] = []

    def add_level(self, num_spots: int):
        level_num = len(self.levels) + 1
        self.levels.append(Level(level_num, num_spots))
        print(f"added level {level_num} with {num_spots} spots")

    def park_vehicle(self, vehicle: Vehicle):
        for level in self.levels:
            spot = level.park_vehicle(vehicle)
            if spot:
                print(f"{vehicle.name} parked at {spot.spot_id}")
                return True
        print(f"no space for {vehicle.name}")
        return False
    
    def unpark_vehicle(self, vehicle: Vehicle):
        for level in self.levels:
            if level.unpark_vehicle(vehicle):
                print(f"{vehicle.name} left")
                return True
        print(f"{vehicle.name} not found")
        return False
    
    def display_availability(self):
        for level in self.levels:
            stats = level.get_availability()
            print(f"level {level.level_number}: {stats}")
            print("-----------")


def demo():
    parking_lot = ParkingLot()
    parking_lot.add_level(5)
    parking_lot.add_level(5)

    c1 = Car("car-1")
    c2 = Car("car-2")

    t1 = Truck("t1")
    t2 = Truck("t2")

    parking_lot.park_vehicle(c1)
    parking_lot.park_vehicle(t1)

    parking_lot.display_availability()

    def parker_worker(v):
        time.sleep(random.uniform(0.1, 0.5))
        parking_lot.park_vehicle(v)

    threads = []
    extra_vehicles = [Car(f"car-X{i}") for i in range(5)]
    
    print("--- Starting Concurrent Parking ---")
    for v in extra_vehicles:
        t = threading.Thread(target=parker_worker, args=(v,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    parking_lot.display_availability()

    parking_lot.unpark_vehicle(c1)
    parking_lot.unpark_vehicle(t1)
    
    parking_lot.display_availability()
if __name__ == "__main__":
    demo()