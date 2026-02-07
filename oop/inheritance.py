class Car:
    def __init__(self):
        self.make = None
        self.model = None
    
    def start_engine(self):
        print("engine started")
    
    def stop_engine(self):
        print("engine stopped")

class ElectricCar(Car):
    def change_battery(self):
        print("battery cahnged")

class GasCar(Car):
    def fill_tank(self):
        print("gas filled")

if __name__ == "__main__":
    e = ElectricCar()
    g = GasCar()

    e.model = "tata"
    e.start_engine()

    g.model = "toyota"
    g.start_engine()

    e.change_battery()
    g.fill_tank()

    e.stop_engine()
    g.stop_engine()