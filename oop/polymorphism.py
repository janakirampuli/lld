# compile time polymorphism (method overloading)

class MathOps:
    def add(self, a, b, c=0):
        return a + b + c
    
math = MathOps()
print(math.add(5, 10))
print(math.add(5, 10, 15))

# run time polymorphism (method overriding)

class Animal:
    def make_sound(self):
        print("blahh")

class Dog(Animal):
    def make_sound(self):
        print("boww")

class Cat(Animal):
    def make_sound(self):
        print("meow")

d = Dog()
d.make_sound()

c = Cat()
c.make_sound()