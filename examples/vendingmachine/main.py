'''

requirements:
1. vending machine should support multiple products with different prices and quantities
2. the machine should accept coins and notes of different denominations
3. admin can restock products, collect the accumulated money
4. concurrency: multiple users at machines
5. data consistency on inventory and cash register

core entities:

VendineMachine
Product
Slot
Inventory
CashRegister
Denomination
Transaction

enums:
MachineState: IDLE, ACCEPTING_MONEY, DISPENSING, OUT_OF_SERVICE
Denomination: COIN_1, COIN_2, COIN_5, COIN_10, NOTE_20, NOTE_50, NOTE_100
TransactionStatus: IN_PROGRESS, COMPLETED, CANCELLED, FAILED

state machine:
IDLE -> user inserts money -> ACCEPTING_MONEY
    insert more | select product
        out of stock | insufficent funds | success
        return $ -> IDLE | prompt user to add more -> ACCPTING_MONEY | DISPENSING -> dispense + change -> IDLE

    cancel at any point in ACCEPTING_MONEY -> return all inserted -> IDLE

classes and interfaces:

VendingMachineState(ABC):
- insert_money(machine, denomination)
- select_product(machine, slot_code)
- cancel(machine)
- dispense(machine)

ChangeStrtegy(ABC):
- make_change(amount, available)

Denomination:
- COIN_1 = 1
- COIN_2 = 2
- COIN_5 = 5
- COIN_10 = 10
- NOTE_20 = 20
- NOTE_50 = 50
- NOTE_100 = 100

Product:
- product_id
- name
- price

Slot:
- slot_code
- product
- quantity
- is_available()

Inventory:
- slots
- get_slot(slot_code)
- get_all_available()
- restock(slot_code, product, quantity)

CashRegister:
- denominations: dict[Denomination, int]
- total_amount()
- add(denomination, count)
- remove(denomination, count)
- get_available()
- collect_all()

Transaction:
- transaction_id
- inserted_amount
- total_inserted()
- selected_slot
- status
- change_returned
- created_at

IdleState(VendingMachineState):
- insert_money()
- select_product: error
- cancel: no-op
- dispense: error

AcceptingMoneyState(VendingMachineState):
- insert_money()
- select_product(slot_code)
- cancel: return inserted money -> IdleState
- dispense: error

DispensingState(VendingMachineState):
- insert_money: error
- select_product: error
- cancel: error(too late)
- dispense: reduce inventory -> move money to register -> IdleState

VendingMachine:
- machine_id
- state
- inventory
- cash_register
- current_transaction
- lock
- insert_money(denomination)
- select_product(slot_code)
- cancel()
- dispense()
- get_display()
- restock(slot_code, product, quantity)
- collect_money()
- set_out_of_service()

GreedyChangeStrategy(ChangeStartegy):
- make_change(amount, available)

'''

from typing import List, Dict
from enum import Enum
import threading
from abc import ABC, abstractmethod

class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

class Coin(Enum):
    ONE = 1
    TWO = 2
    FIVE = 5

class Note(Enum):
    TEN = 10
    FIFTY = 50
    HUNDRED = 100

class Inventory:
    def __init__(self):
        self.products: Dict[Product, int] = {}
        self.lock = threading.Lock()

    def add_product(self, product: Product, quantity: int):
        with self.lock:
            self.products[product] = self.products.get(product, 0) + quantity
            print(f"added {product.name} - {quantity}")

    def remove_product(self, product: Product):
        with self.lock:
            if product in self.products:
                if self.products[product] > 0:
                    self.products[product] -= 1
                    return True
        return False
            

    def get_quantity(self, product: Product):
        with self.lock:
            return self.products.get(product, 0)


class VendingMachineState(ABC):
    @abstractmethod
    def select_product(self, machine, product: Product):
        pass

    @abstractmethod
    def insert_money(self, machine, amount: int):
        pass

    @abstractmethod
    def dispense_product(self, machine):
        pass

    @abstractmethod
    def decline_transaction(self, machine):
        pass

class IdleState(VendingMachineState):
    def select_product(self, machine, product: Product):
        if machine.inventory.products[product] > 0:
            machine.selected_product = product
            machine.set_state(machine.ready_state)
            print(f"selected {product.name}")
        else:
            print(f"product not found")

    def insert_money(self, machine, amount):
        print(f"please select product first")

    def dispense_product(self, machine):
        print(f"please select product first")

    def decline_transaction(self, machine):
        print(f"please select product first")

class ReadyState(VendingMachineState):
    def select_product(self, machine, product: Product):
        print(f"product already selected")

    def insert_money(self, machine, amount):
        machine.balance += amount
        print(f"inserted {amount}")
        if machine.balance >= machine.selected_product.price:
            machine.set_state(machine.dispense_state)
            machine.state.dispense_product(machine)

    def dispense_product(self, machine):
        print(f"insert enough money")


    def decline_transaction(self, machine):
        print(f"transaction declined")
        machine.selected_product = None
        machine.balance = 0

class DispenseState(VendingMachineState):
    def select_product(self, machine, product: Product):
        print(f"product already selected")

    def insert_money(self, machine, amount):
        print("wait - dispensing product")

    def dispense_product(self, machine):
        product = machine.selected_product

        if machine.inventory.remove_product(product):
            change = machine.balance - product.price
            print("dispensing...")
            print(f"change - {change}")
            machine.selected_product = None
            machine.balance = 0
            machine.set_state(machine.idle_state)
        else:
            print("item out of stock, refunding {machine.balance}")
            machine.selected_product = None
            machine.balance = 0
            machine.set_state(machine.idle_state)


    def decline_transaction(self, machine):
        print(f"transaction declined")
        machine.selected_product = None
        machine.balance = 0

class VendingMachine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VendingMachine, cls).__new__(cls)
                    cls._instance._initialize()

        return cls._instance
    
    def _initialize(self):
        self.inventory: Inventory = Inventory()
        self.ready_state = ReadyState()
        self.idle_state = IdleState()
        self.dispense_state = DispenseState()
        self.state: VendingMachineState = self.idle_state
        self.selected_product: Product = None
        self.balance = 0

    def set_state(self, state: VendingMachineState):
        self.state = state

    def select_product(self, product: Product):
        self.state.select_product(self, product)

    def insert_coin(self, coin: Coin):
        self.state.insert_money(self, coin.value)

    def insert_note(self, note: Note):
        self.state.insert_money(self, note.value)

    def cancel_transaction(self):
        self.state.decline_transaction(self)

    def repr(self):
        for p, q in self.inventory.products.items():
            print(p.name, q)

    
def demo():
    vm = VendingMachine()
    sprite = Product("sprite", 10)
    coke = Product("coke", 12)
    lays = Product("lays", 15)

    vm.inventory.add_product(sprite, 2)
    vm.inventory.add_product(coke, 1)
    vm.inventory.add_product(lays, 5)

    vm.select_product(lays)
    vm.insert_coin(Coin.FIVE)
    vm.insert_note(Note.TEN)
    vm.repr()


    vm.select_product(lays)
    vm.insert_coin(Coin.FIVE)
    vm.cancel_transaction()
    vm.repr()


if __name__ == "__main__":
    demo()