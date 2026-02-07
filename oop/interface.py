from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def initialize_payment(self, amount):
        pass

class Stripe(PaymentGateway):
    def initialize_payment(self, amount):
        print(f"using stripe for ${amount}")

class RazorPay(PaymentGateway):
    def initialize_payment(self, amount):
        print(f"using razorpay for ${amount}")

class CheckoutService:
    def __init__(self, payment_gateway):
        self.payment_gateway = payment_gateway

    def set_payment_gateway(self, payment_gateway):
        self.payment_gateway = payment_gateway

    def checkout(self, amount):
        self.payment_gateway.initialize_payment(amount)

if __name__ == "__main__":
    stripe = Stripe()
    checkout = CheckoutService(stripe)
    checkout.checkout(10)

    razorpay = RazorPay()
    checkout.set_payment_gateway(razorpay)
    checkout.checkout(20)