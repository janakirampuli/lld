class BankAccount:
    def __init__(self):
        self.__balance = 0
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("deposit should be +ve")
        self.__balance += amount
    
    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("witdraw should be +ve")
        if amount > self.__balance:
            raise ValueError("insufficient funds")
        self.__balance -= amount

    def get_balance(self):
        return self.__balance
    
if __name__ == "__main__":
    account = BankAccount()
    print(account.get_balance())
    account.deposit(10)
    print(account.get_balance())
    account.withdraw(5)
    print(account.get_balance())
    # print(account.__balance) # error
    # print(account._BankAccount__balance) # correct
