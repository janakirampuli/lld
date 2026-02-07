from enum import Enum

class OrderStatus(Enum):
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class Coin(Enum):
    PENNY = 1
    NICKEL = 5
    DIME = 10
    QUARTER = 25

    def __init__(self, value):
        self.coin_value = value
    
    def get_value(self):
        return self.coin_value

if __name__ == "__main__":
    status = OrderStatus.PLACED
    print(status)

    total = Coin.PENNY.get_value() + Coin.NICKEL.get_value()
    print(total)