'''

requirements:
1. multiple elevators, multiple floors
2. user presses button on floor(UP/DOWN) -> system assigns best elevator
3. user enters elevator -> selects destination floor
4. capacity limit per elevator
5. optimal assignment: minimize the wait time
6. thread-safe: multiple concurrent requests
7. efficient order of stops per elevator

core entities:

ElevatorSystem
Elevator
Floor
Request
Door
Display

enums:

Direction: UP, DOWN
ElevatorStatus: MOVING, STOPPED, MAINTENACE, OUT_OF_SERVICE
DoorStatus: OPEN, CLOSED
RequestType: EXTERNAL, INTERNAL

classes and interfaces:

ElevatorAssignmentStrategy
- assign(request, elevators)

RequestScheduler:
- schedule(elevator, floor)
- get_next_stop(elevator)

Floor:
- floor_number
- up_button
- down_button
- display

Display:
- current_floor
- update(floor, direction)

Door:
- status
- open()
- close()

Elevator:
- elevator_id
- current_floor
- direction
- status
- capacity
- current_load
- door
- display
- scheduler
- is_full()
- add_stop(floor)
- get_next_stop()
- move()

ExternalRequest:
- source_floor
- direction
- timestamp

InternalRequest:
- elevator_id
- destination_floor
- timestamp

Scheduling:
LookScheduler(RequestScheduler):
- up_stops
- down_stops
schedule(elevator, floor): add floor to approriate set based on ellevators current direction and floor's relative position
- get_next_stop(elevator):

ElevatorSystem
- elevators
- floors
- assignment_startegy
- request_queue
- request_elevator(floor, direction)
- select_floor(elevator_id, floor)
- process_requests()

NearestElevatorStrategy(ElevatorAssignmentStrategy):
- assign(request, elevators)
    filter not full, not in maontenance
    prefer elevator already moving toward request floor
    tiebreak: smallest absolute distance
    fallback: most IDLE elevator
    scoring: score = distance + direction_penalty


concurrency:
each elevator runs on its own thread, continuously calling move() in loop
external/internal requests are pushed to request_queue
    



    
'''

from enum import Enum
from typing import List, Set
import threading
import time

class Direction(Enum):
    UP = 1
    DOWN = 2
    IDLE = 3

class Elevator:
    def __init__(self, id: int, capacity: int):
        self.id = id
        self.capacity = capacity
        self.current_floor = 0
        self.current_load = 0
        self.direction: Direction = Direction.IDLE
        self.stops: Set[int] = set()
        
        self.lock = threading.Lock()
        self.is_running = True
        self.thread = threading.Thread(target=self.run_loop)
        self.thread.start()

    def add_stop(self, floor: int):
        with self.lock:
            self.stops.add(floor)

            if self.direction == Direction.IDLE:
                if floor > self.current_floor:
                    self.direction = Direction.UP
                elif floor < self.current_floor:
                    self.direction = Direction.DOWN

    def open_doors(self):
        print(f"elevator {self.id} opened at {self.current_floor}")

    def run_loop(self):
        while self.is_running:
            with self.lock:
                if self.current_floor in self.stops:
                    self.open_doors()
                    self.stops.remove(self.current_floor)
                if not self.stops:
                    self.direction = Direction.IDLE
                else:
                    self.move_next_step()
            time.sleep(1)
    
    def move_next_step(self):
        if self.direction == Direction.UP:
            if any(f > self.current_floor for f in self.stops):
                self.current_floor += 1
                print(f"elevator {self.id} moving up to {self.current_floor}")
            else:
                self.direction = Direction.DOWN

        elif self.direction == Direction.DOWN:
            if any(f < self.current_floor for f in self.stops):
                self.current_floor -= 1
                print(f"elevator {self.id} moving down to {self.current_floor}")
            else:
                self.direction = Direction.UP
        


    
class ElevatorController:
    def __init__(self, num_elevators: int, capacity: int):
        self.elevators: List[Elevator] = [Elevator(i, capacity) for i in range(num_elevators)]
    
    def request_elevator(self, src: int, dest: int):
        print(f"request from {src} to {dest}")
        best_elevator = self.find_optimal_elevator(src, dest)
        best_elevator.add_stop(src)
        best_elevator.add_stop(dest)

    def find_optimal_elevator(self, src: int, dest: int):
        best_elevator = None

        req_direction = Direction.UP if dest > src else Direction.DOWN

        min_score = float("inf")
        for elevator in self.elevators:
            score = float("inf")

            with elevator.lock:
                curr = elevator.current_floor
                dir = elevator.direction

                if dir == Direction.IDLE:
                    score = abs(dest - src)
                elif dir == Direction.UP and src >= curr:
                    score = src - curr
                elif dir == Direction.DOWN and src <= curr:
                    if req_direction == Direction.DOWN:
                        score = curr - src
                    else:
                        score = curr - src + 5
                else:
                    score = abs(curr - src) + 20

            if score < min_score:
                min_score = score
                best_elevator = elevator
        return best_elevator
    

def demo():
    controller = ElevatorController(2, 10)
    time.sleep(1)
    controller.request_elevator(0, 5)
    time.sleep(5)
    controller.request_elevator(1, 6)

if __name__ == "__main__":
    demo()