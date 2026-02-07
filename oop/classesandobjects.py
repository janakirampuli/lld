class Car:
    def __init__(self, brand, model):
        self._brand = brand
        self._model = model
        self._speed = 0

    def accelerate(self, inc):
        self._speed += inc
    
    def display_status(self):
        print(f"{self._brand}, {self._speed}")

if __name__ == "__main__":
    corolla = Car("totyota", "corolla")
    mustang = Car("ford", "mustanf")

    corolla.accelerate(10)
    mustang.accelerate(20)

    corolla.display_status()
    mustang.display_status()


# self.brand (Public): "This is public data. Go ahead and read/write this directly from outside the class."

# self._brand (Non-Public/Protected): "This is for internal use. Please do not touch this directly from outside the class. Use a method (getter/setter) if you need to access it."