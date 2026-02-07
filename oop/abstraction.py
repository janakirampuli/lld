from abc import ABC, abstractmethod

# abstract classes

class Vehicle(ABC):
    def __init__(self, brand):
        self.brand = brand

    @abstractmethod
    def start(self):
        pass

    def display_brand(self):
        print(f"brand: {self.brand}")

class Car(Vehicle):
    def __init__(self, brand):
        super().__init__(brand)

    def start(self):
        print("car started")

# Interfaces

class Document:
    def __init__(self, content):
        self.__content = content
    
    def get_content(self):
        return self.__content
    
class Printable(ABC):
    @abstractmethod
    def print(self, document):
        pass

class PDFPrinter(Printable):
    def print(self, document):
        print(f"printing pdf: {document.get_content()}")
    
class InkPrinter(Printable):
    def print(self, document):
        print(f"priniting via ink: {document.get_content()}")

if __name__ == "__main__":
    c = Car("tata")
    c.display_brand()
    c.start()

    pdf = PDFPrinter()
    doc = Document("abcd")
    pdf.print(doc)