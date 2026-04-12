'''

requirements:
1. process payments via multiple gateways
2. support multiple payment methods
3. support multiple currencies
4. handle refunds
5. track transaction life cycle
6. idempotency
7. concurrent payment requests - no double charge


core entities:
PaymentRequest
Transaction
PaymentDetails
Refund
TransactionLog
GatewayResponse

enums:
PaymentStatus: PENDING, SUCCESS, FAILED, REFUNDED
Currency: INR, USD, EUR
PaymentMethod: CREDIT_CARD, DEBIT_CARD, UPI, NET_BANKING
GatewayType: STRIPE, RAZORPAY
RefundStatus: PENDING, SUCCESS, FAILED
TransactionLogType: CREATED, GATEWAY_REQUESTED, GATEWAY_RESPONSE, STATUS_CHANGED, REFUND_INITIATED, REFUND_COMPLETED, RETRY

PaymentGateway(ABC):
- gateway_type
- process_payment(payment_details, amount, currency)
- process_refund(gateway_transaction_id, amount, currency)
- check_status(gateway_transaction_id)

GatewayRouter(ABC):
- route(request)

IdempotencyStrategy(ABC):
- exists(idempotency_key)
- get(idempotency_key)
- store(idempotency_key, transaction)

PaymentDetails:
- method
- card_number
- card_expiry
- upi_id
- bank_code

PaymentRequest:
- request_id
- idempotency_key
- user_id
- amount
- currency
- payment_details
- description
- metadata

GatewayResponse:
- success
- gateway_transaction_id
- gateway_type
- status_code
- error_message
- raw_response

Transaction:
- log_id
- transaction_id
- log_type
- old_status
- new_status
- gateway_response
- message
- timestamp

Refund:
- refund_id
- transaction_id
- amount
- status
- gateway_refund_id
- reason
- created_at

StripeGateway(PaymentGateway):
- gateway_type
- process_payment
- process_refund
- check_status

RazorpayGateway(PaymentGateway):
- gateway_type
- process_payment
- process_refund
- check_status

PaymentService:
- router
- idempotency_store
- transaction_store
- transaction_locks
- max_retries




'''
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional
import uuid
from datetime import datetime

# --- Enums ---

class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class Currency(Enum):
    USD = "USD"
    INR = "INR"
    EUR = "EUR"

class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    UPI = "UPI"
    PAYPAL = "PAYPAL"

# --- Models ---

class PaymentDetails:
    """Holds the sensitive/specific info for the payment (e.g., card number, UPI ID)."""
    def __init__(self, method: PaymentMethod, data: dict):
        self.method = method
        self.data = data # In a real system, this would be heavily encrypted/tokenized

class Transaction:
    def __init__(self, user_id: str, amount: float, currency: Currency):
        self.transaction_id = f"txn_{uuid.uuid4().hex[:10]}"
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        self.status = PaymentStatus.PENDING
        self.gateway_reference: Optional[str] = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def mark_success(self, gateway_ref: str):
        self.status = PaymentStatus.SUCCESS
        self.gateway_reference = gateway_ref
        self.updated_at = datetime.now()

    def mark_failed(self):
        self.status = PaymentStatus.FAILED
        self.updated_at = datetime.now()

# --- External Gateway Strategies ---

class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, transaction: Transaction, details: PaymentDetails) -> bool:
        """
        Communicates with the external provider. 
        Returns True if successful, False otherwise.
        """
        pass

class StripeGateway(PaymentGateway):
    def process_payment(self, transaction: Transaction, details: PaymentDetails) -> bool:
        print(f"[Stripe] Processing {transaction.amount} {transaction.currency.value} for {transaction.user_id}...")
        # Simulate network call and logic
        if details.method not in [PaymentMethod.CREDIT_CARD]:
            print("[Stripe] Error: Unsupported payment method.")
            return False
        
        # Simulating a successful external call
        fake_stripe_ref = f"ch_{uuid.uuid4().hex[:8]}"
        transaction.mark_success(fake_stripe_ref)
        return True

class RazorpayGateway(PaymentGateway):
    def process_payment(self, transaction: Transaction, details: PaymentDetails) -> bool:
        print(f"[Razorpay] Processing {transaction.amount} {transaction.currency.value} for {transaction.user_id}...")
        # Simulate network call
        fake_rp_ref = f"pay_{uuid.uuid4().hex[:8]}"
        transaction.mark_success(fake_rp_ref)
        return True

# --- Factory / Router ---

class GatewayRouter:
    def __init__(self):
        self.gateways = {
            "STRIPE": StripeGateway(),
            "RAZORPAY": RazorpayGateway()
        }

    def route(self, currency: Currency, method: PaymentMethod) -> PaymentGateway:
        """
        Business rule: Route INR and UPI to Razorpay, everything else to Stripe.
        """
        if currency == Currency.INR or method == PaymentMethod.UPI:
            return self.gateways["RAZORPAY"]
        return self.gateways["STRIPE"]

# --- Core Service / Facade ---

class PaymentService:
    def __init__(self, router: GatewayRouter):
        self.router = router
        self.transaction_ledger: Dict[str, Transaction] = {}

    def initiate_payment(self, user_id: str, amount: float, currency: Currency, details: PaymentDetails) -> Transaction:
        # 1. Create a Pending Transaction (Idempotency key origin)
        transaction = Transaction(user_id, amount, currency)
        self.transaction_ledger[transaction.transaction_id] = transaction
        
        # 2. Determine which gateway to use via the Router
        gateway = self.router.route(currency, details.method)
        
        # 3. Process the payment
        print(f"\nInitiating Txn: {transaction.transaction_id} | Routing to: {type(gateway).__name__}")
        try:
            success = gateway.process_payment(transaction, details)
            if not success:
                transaction.mark_failed()
        except Exception as e:
            print(f"System error during payment: {e}")
            transaction.mark_failed()

        # 4. Return the transaction state to the client
        return transaction

    def get_transaction(self, txn_id: str) -> Optional[Transaction]:
        return self.transaction_ledger.get(txn_id)

# --- Demo / Driver Code ---

def demo():
    router = GatewayRouter()
    payment_service = PaymentService(router)

    # User 1: Pays in USD using Credit Card (Should route to Stripe)
    usd_details = PaymentDetails(PaymentMethod.CREDIT_CARD, {"card_no": "1234-5678-9012-3456"})
    txn1 = payment_service.initiate_payment("user_101", 99.99, Currency.USD, usd_details)
    print(f"Result -> Status: {txn1.status.value}, Ref: {txn1.gateway_reference}")

    # User 2: Pays in INR using UPI (Should route to Razorpay)
    inr_details = PaymentDetails(PaymentMethod.UPI, {"vpa": "user@okbank"})
    txn2 = payment_service.initiate_payment("user_102", 1500.00, Currency.INR, inr_details)
    print(f"Result -> Status: {txn2.status.value}, Ref: {txn2.gateway_reference}")

    # User 3: Tries an unsupported method on Stripe (USD with UPI - simulated failure)
    bad_details = PaymentDetails(PaymentMethod.UPI, {"vpa": "user@okbank"})
    txn3 = payment_service.initiate_payment("user_103", 50.00, Currency.USD, bad_details)
    print(f"Result -> Status: {txn3.status.value}, Ref: {txn3.gateway_reference}")

if __name__ == "__main__":
    demo()