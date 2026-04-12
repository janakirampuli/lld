'''

requirements:
1. users can search flights by source, destination, date
2. book a flight -> select a seat -> pay
3. cancel/modify the booking -> refund
4. admin manages flights, aircraft, crew
5. passenger manages profile, baggage
6. concurrency: 2 users can't book same seat
7. scalability: new airlines, routes, payment methods

core entities:
User
Flight
FlightSchedule
Aircraft
Seat
Booking
Payment
Passenger
Baggage
FlightSearch

Enums:
BookingStatus: CONFIRMED, CANCELLED, PENDING, COMPLETED
SeatType: ECONOMy, BUSSINESS, FIRST_CLASS
SeatStatus: AVAILABLE, BOOKED, BLOCKED
PaymentStatus: SUCCESS, FAILED, REFUNDED, PENDING
PaymentMethod: CREDIT_CARD, DEBIT_CARD, UPI, WALLET
FlightStatus: SCHEDULED, DELAYED, CANCELLED, COMPLETED
UserRole: PASSENGER, STAFF, ADMIN

Classes:
User
- user_id
- email
- name
- role: UserRole

Passenger extends User:
- passport_number
- baggage
- bookings: List[Booking]

Staff extends User:
- employee_id
- designation

Admin extends User:
- employee_id

Aircraft:
- aircraft_id
- model
- total_seats
- seats: List[Seat]

Seat:
- seat_id
- type: SeatType
- status: SeatStatus
- price

Flight:
- flight_id
- flight_number
- source
- destination
- departure_time
- arrival_time
- aircraft: Aircraft
- status: FlightStatus
- crew: List[Staff]

Booking:
- booking_id
- passenger
- flight
- seat
- payment
- status
- booking_time
- baggage

Baggage:
- baggage_id
- weight

Payment:
- payment_id
- amount
- method
- status
- transaction_time

FlightSearchCriteria:
- source
- destination
- date

Interfaces:

FlightSearch:
- search(source, destination, date) -> List[Flight]

BookingService:
- createBooking(passenger, flight, seat, payment) -> Booking
- cancelBooking(booking_id)
- modifyBooking(booking_id, new_flight, new_seat)

PaymentProcessor:
- processPayment(amount, method)
- processRefund(payment_id, amount)

SeatManager:
- getAvailableSeats(flight_id)
- lockSeat(flight_id, seat_id)
- bookSeat(flight_id, seat_id)
- releaseSeat(flight_id, seat_id)

NotificationService:
- notify(user_id, message)

Service classes:

AirlineManagementSystem:
- manages BookingService, FlightSearch, SeatManager, FlightManager
- entry point for all ops

FlightManager:
- addFlight(flight)
- cancelFlight(flight)
- assignCrew(flight_id, staff)
- assignAircraft(flight_id, aircraft)
- flights: dict[flight_id, Flight]

BookingServiceImpl:
- lock seat -> process payment -> confirm booking
- bookings: dictp[booking_id, Booking]

SeatManagerServiceImpl:
- seats: dict[flight_id : {seat_id: Seat}]
- threading.Lock per seat concurrency


'''
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
import threading
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


class BookingException(Exception):
    pass


class FlightNotFoundException(Exception):
    pass


class SeatUnavailableException(Exception):
    pass


class PaymentException(Exception):
    pass


class BookingStatus(Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class SeatType(Enum):
    ECONOMY = "ECONOMY"
    BUSSINESS = "BUSSINESS"
    BUSINESS = "BUSSINESS"  # alias kept for typo compatibility
    FIRST_CLASS = "FIRST_CLASS"


class SeatStatus(Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"


class PaymentStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PENDING = "PENDING"


class PaymentMethod(Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    UPI = "UPI"
    WALLET = "WALLET"


class FlightStatus(Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class UserRole(Enum):
    PASSENGER = "PASSENGER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


@dataclass
class User:
    email: str
    name: str
    role: UserRole
    user_id: str = field(default_factory=_new_id)


@dataclass
class Baggage:
    weight: float
    baggage_id: str = field(default_factory=_new_id)


@dataclass
class Passenger(User):
    passport_number: str = ""
    baggage: List[Baggage] = field(default_factory=list)
    bookings: List["Booking"] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.role = UserRole.PASSENGER


@dataclass
class Staff(User):
    employee_id: str = ""
    designation: str = ""

    def __post_init__(self) -> None:
        self.role = UserRole.STAFF


@dataclass
class Admin(User):
    employee_id: str = ""

    def __post_init__(self) -> None:
        self.role = UserRole.ADMIN


@dataclass
class Seat:
    seat_id: str
    type: SeatType
    price: float
    status: SeatStatus = SeatStatus.AVAILABLE


@dataclass
class Aircraft:
    model: str
    seats: List[Seat]
    aircraft_id: str = field(default_factory=_new_id)
    total_seats: int = 0

    def __post_init__(self) -> None:
        self.total_seats = len(self.seats)


@dataclass
class Flight:
    flight_number: str
    source: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    aircraft: Aircraft
    status: FlightStatus = FlightStatus.SCHEDULED
    crew: List[Staff] = field(default_factory=list)
    flight_id: str = field(default_factory=_new_id)


@dataclass
class FlightSchedule:
    flight: Flight
    operating_date: date


@dataclass
class Payment:
    amount: float
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_time: datetime = field(default_factory=datetime.now)
    payment_id: str = field(default_factory=_new_id)


@dataclass
class Booking:
    passenger: Passenger
    flight: Flight
    seat: Seat
    payment: Payment
    status: BookingStatus
    baggage: List[Baggage]
    booking_time: datetime = field(default_factory=datetime.now)
    booking_id: str = field(default_factory=_new_id)


@dataclass
class FlightSearchCriteria:
    source: str
    destination: str
    date: date


class FlightSearch(ABC):
    @abstractmethod
    def search(self, source: str, destination: str, when: date) -> List[Flight]:
        pass


class BookingService(ABC):
    @abstractmethod
    def create_booking(
        self,
        passenger: Passenger,
        flight: Flight,
        seat_id: str,
        payment_method: PaymentMethod,
        baggage: Optional[List[Baggage]] = None,
    ) -> Booking:
        pass

    @abstractmethod
    def cancel_booking(self, booking_id: str) -> Booking:
        pass

    @abstractmethod
    def modify_booking(self, booking_id: str, new_flight: Flight, new_seat_id: str) -> Booking:
        pass

    # camelCase compatibility names from the docstring
    def createBooking(self, passenger: Passenger, flight: Flight, seat: str, payment: PaymentMethod) -> Booking:
        return self.create_booking(passenger, flight, seat, payment)

    def cancelBooking(self, booking_id: str) -> Booking:
        return self.cancel_booking(booking_id)

    def modifyBooking(self, booking_id: str, new_flight: Flight, new_seat: str) -> Booking:
        return self.modify_booking(booking_id, new_flight, new_seat)


class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount: float, method: PaymentMethod) -> Payment:
        pass

    @abstractmethod
    def process_refund(self, payment_id: str, amount: float) -> Payment:
        pass

    # camelCase compatibility names from the docstring
    def processPayment(self, amount: float, method: PaymentMethod) -> Payment:
        return self.process_payment(amount, method)

    def processRefund(self, payment_id: str, amount: float) -> Payment:
        return self.process_refund(payment_id, amount)


class SeatManager(ABC):
    @abstractmethod
    def get_available_seats(self, flight_id: str) -> List[Seat]:
        pass

    @abstractmethod
    def lock_seat(self, flight_id: str, seat_id: str) -> bool:
        pass

    @abstractmethod
    def book_seat(self, flight_id: str, seat_id: str) -> None:
        pass

    @abstractmethod
    def release_seat(self, flight_id: str, seat_id: str) -> None:
        pass

    # camelCase compatibility names from the docstring
    def getAvailableSeats(self, flight_id: str) -> List[Seat]:
        return self.get_available_seats(flight_id)

    def lockSeat(self, flight_id: str, seat_id: str) -> bool:
        return self.lock_seat(flight_id, seat_id)

    def bookSeat(self, flight_id: str, seat_id: str) -> None:
        self.book_seat(flight_id, seat_id)

    def releaseSeat(self, flight_id: str, seat_id: str) -> None:
        self.release_seat(flight_id, seat_id)


class NotificationService(ABC):
    @abstractmethod
    def notify(self, user_id: str, message: str) -> None:
        pass


class ConsoleNotificationService(NotificationService):
    def notify(self, user_id: str, message: str) -> None:
        print(f"[Notification][user={user_id}] {message}")


class FlightManager:
    def __init__(self) -> None:
        self.flights: Dict[str, Flight] = {}

    def add_flight(self, flight: Flight) -> None:
        self.flights[flight.flight_id] = flight

    def cancel_flight(self, flight_id: str) -> None:
        flight = self.get_flight(flight_id)
        flight.status = FlightStatus.CANCELLED

    def assign_crew(self, flight_id: str, staff: Staff) -> None:
        flight = self.get_flight(flight_id)
        flight.crew.append(staff)

    def assign_aircraft(self, flight_id: str, aircraft: Aircraft) -> None:
        flight = self.get_flight(flight_id)
        flight.aircraft = aircraft

    def get_flight(self, flight_id: str) -> Flight:
        flight = self.flights.get(flight_id)
        if not flight:
            raise FlightNotFoundException(f"Flight not found: {flight_id}")
        return flight

    # camelCase compatibility names from the docstring
    def addFlight(self, flight: Flight) -> None:
        self.add_flight(flight)

    def cancelFlight(self, flight: Flight) -> None:
        self.cancel_flight(flight.flight_id)

    def assignCrew(self, flight_id: str, staff: Staff) -> None:
        self.assign_crew(flight_id, staff)

    def assignAircraft(self, flight_id: str, aircraft: Aircraft) -> None:
        self.assign_aircraft(flight_id, aircraft)


class FlightSearchServiceImpl(FlightSearch):
    def __init__(self, flight_manager: FlightManager) -> None:
        self.flight_manager = flight_manager

    def search(self, source: str, destination: str, when: date) -> List[Flight]:
        matches: List[Flight] = []
        for flight in self.flight_manager.flights.values():
            if (
                flight.source == source
                and flight.destination == destination
                and flight.departure_time.date() == when
                and flight.status != FlightStatus.CANCELLED
            ):
                matches.append(flight)
        return matches


class SeatManagerServiceImpl(SeatManager):
    def __init__(self) -> None:
        self.seats: Dict[str, Dict[str, Seat]] = {}
        self._seat_locks: Dict[str, Dict[str, threading.Lock]] = {}

    def register_flight(self, flight: Flight) -> None:
        seat_map = {seat.seat_id: seat for seat in flight.aircraft.seats}
        self.seats[flight.flight_id] = seat_map
        self._seat_locks[flight.flight_id] = {seat_id: threading.Lock() for seat_id in seat_map}

    def get_available_seats(self, flight_id: str) -> List[Seat]:
        return [seat for seat in self._get_flight_seat_map(flight_id).values() if seat.status == SeatStatus.AVAILABLE]

    def lock_seat(self, flight_id: str, seat_id: str) -> bool:
        seat = self._get_seat(flight_id, seat_id)
        lock = self._get_lock(flight_id, seat_id)

        acquired = lock.acquire(blocking=False)
        if not acquired:
            return False

        if seat.status != SeatStatus.AVAILABLE:
            lock.release()
            return False

        seat.status = SeatStatus.BLOCKED
        return True

    def book_seat(self, flight_id: str, seat_id: str) -> None:
        seat = self._get_seat(flight_id, seat_id)
        lock = self._get_lock(flight_id, seat_id)

        if seat.status != SeatStatus.BLOCKED:
            raise SeatUnavailableException(f"Seat {seat_id} is not locked for booking")

        seat.status = SeatStatus.BOOKED
        if lock.locked():
            try:
                lock.release()
            except RuntimeError:
                pass

    def release_seat(self, flight_id: str, seat_id: str) -> None:
        seat = self._get_seat(flight_id, seat_id)
        lock = self._get_lock(flight_id, seat_id)

        if seat.status in (SeatStatus.BLOCKED, SeatStatus.BOOKED):
            seat.status = SeatStatus.AVAILABLE

        if lock.locked():
            try:
                lock.release()
            except RuntimeError:
                pass

    def _get_flight_seat_map(self, flight_id: str) -> Dict[str, Seat]:
        if flight_id not in self.seats:
            raise FlightNotFoundException(f"Flight seats not found: {flight_id}")
        return self.seats[flight_id]

    def _get_seat(self, flight_id: str, seat_id: str) -> Seat:
        seat_map = self._get_flight_seat_map(flight_id)
        seat = seat_map.get(seat_id)
        if not seat:
            raise SeatUnavailableException(f"Seat not found: {seat_id}")
        return seat

    def _get_lock(self, flight_id: str, seat_id: str) -> threading.Lock:
        locks = self._seat_locks.get(flight_id, {})
        lock = locks.get(seat_id)
        if not lock:
            raise SeatUnavailableException(f"No lock configured for seat: {seat_id}")
        return lock


class PaymentProcessorImpl(PaymentProcessor):
    def __init__(self) -> None:
        self.payments: Dict[str, Payment] = {}

    def process_payment(self, amount: float, method: PaymentMethod) -> Payment:
        payment = Payment(amount=amount, method=method, status=PaymentStatus.PENDING)
        payment.status = PaymentStatus.SUCCESS if amount > 0 else PaymentStatus.FAILED
        payment.transaction_time = datetime.now()
        self.payments[payment.payment_id] = payment
        return payment

    def process_refund(self, payment_id: str, amount: float) -> Payment:
        payment = self.payments.get(payment_id)
        if not payment:
            raise PaymentException(f"Payment not found: {payment_id}")

        if payment.status != PaymentStatus.SUCCESS or amount > payment.amount:
            payment.status = PaymentStatus.FAILED
            raise PaymentException("Refund failed due to invalid payment state/amount")

        payment.status = PaymentStatus.REFUNDED
        payment.transaction_time = datetime.now()
        return payment


class BookingServiceImpl(BookingService):
    def __init__(
        self,
        seat_manager: SeatManagerServiceImpl,
        payment_processor: PaymentProcessor,
        notification_service: NotificationService,
    ) -> None:
        self.seat_manager = seat_manager
        self.payment_processor = payment_processor
        self.notification_service = notification_service
        self.bookings: Dict[str, Booking] = {}

    def create_booking(
        self,
        passenger: Passenger,
        flight: Flight,
        seat_id: str,
        payment_method: PaymentMethod,
        baggage: Optional[List[Baggage]] = None,
    ) -> Booking:
        if not self.seat_manager.lock_seat(flight.flight_id, seat_id):
            raise SeatUnavailableException(f"Seat {seat_id} is not available")

        payment: Optional[Payment] = None
        try:
            seat = self.seat_manager._get_seat(flight.flight_id, seat_id)
            payment = self.payment_processor.process_payment(seat.price, payment_method)
            if payment.status != PaymentStatus.SUCCESS:
                raise PaymentException("Payment failed")

            self.seat_manager.book_seat(flight.flight_id, seat_id)

            booking = Booking(
                passenger=passenger,
                flight=flight,
                seat=seat,
                payment=payment,
                status=BookingStatus.CONFIRMED,
                baggage=list(baggage if baggage is not None else passenger.baggage),
            )
            self.bookings[booking.booking_id] = booking
            passenger.bookings.append(booking)
            self.notification_service.notify(passenger.user_id, f"Booking confirmed: {booking.booking_id}")
            return booking
        except Exception as exc:
            if payment and payment.status == PaymentStatus.SUCCESS:
                try:
                    self.payment_processor.process_refund(payment.payment_id, payment.amount)
                except Exception:
                    pass
            self.seat_manager.release_seat(flight.flight_id, seat_id)
            raise BookingException(f"Booking failed: {exc}") from exc

    def cancel_booking(self, booking_id: str) -> Booking:
        booking = self._get_booking(booking_id)
        if booking.status != BookingStatus.CONFIRMED:
            raise BookingException("Only confirmed bookings can be cancelled")

        self.payment_processor.process_refund(booking.payment.payment_id, booking.payment.amount)
        self.seat_manager.release_seat(booking.flight.flight_id, booking.seat.seat_id)
        booking.status = BookingStatus.CANCELLED
        self.notification_service.notify(booking.passenger.user_id, f"Booking cancelled: {booking.booking_id}")
        return booking

    def modify_booking(self, booking_id: str, new_flight: Flight, new_seat_id: str) -> Booking:
        old_booking = self._get_booking(booking_id)
        if old_booking.status != BookingStatus.CONFIRMED:
            raise BookingException("Only confirmed bookings can be modified")

        new_booking = self.create_booking(
            passenger=old_booking.passenger,
            flight=new_flight,
            seat_id=new_seat_id,
            payment_method=old_booking.payment.method,
            baggage=old_booking.baggage,
        )

        try:
            self.cancel_booking(old_booking.booking_id)
            old_booking.status = BookingStatus.COMPLETED
            self.notification_service.notify(
                old_booking.passenger.user_id,
                f"Booking modified: {old_booking.booking_id} -> {new_booking.booking_id}",
            )
            return new_booking
        except Exception as exc:
            self.cancel_booking(new_booking.booking_id)
            raise BookingException(f"Modification failed and rolled back: {exc}") from exc

    def _get_booking(self, booking_id: str) -> Booking:
        booking = self.bookings.get(booking_id)
        if not booking:
            raise BookingException(f"Booking not found: {booking_id}")
        return booking


class AirlineManagementSystem:
    def __init__(self) -> None:
        self.flight_manager = FlightManager()
        self.seat_manager = SeatManagerServiceImpl()
        self.flight_search = FlightSearchServiceImpl(self.flight_manager)
        self.payment_processor = PaymentProcessorImpl()
        self.notification_service = ConsoleNotificationService()
        self.booking_service = BookingServiceImpl(
            seat_manager=self.seat_manager,
            payment_processor=self.payment_processor,
            notification_service=self.notification_service,
        )

    def add_flight(self, flight: Flight) -> None:
        self.flight_manager.add_flight(flight)
        self.seat_manager.register_flight(flight)

    def search_flights(self, criteria: FlightSearchCriteria) -> List[Flight]:
        return self.flight_search.search(criteria.source, criteria.destination, criteria.date)

    def book_flight(
        self,
        passenger: Passenger,
        flight_id: str,
        seat_id: str,
        payment_method: PaymentMethod,
        baggage: Optional[List[Baggage]] = None,
    ) -> Booking:
        flight = self.flight_manager.get_flight(flight_id)
        return self.booking_service.create_booking(passenger, flight, seat_id, payment_method, baggage=baggage)

    def cancel_booking(self, booking_id: str) -> Booking:
        return self.booking_service.cancel_booking(booking_id)

    def modify_booking(self, booking_id: str, new_flight_id: str, new_seat_id: str) -> Booking:
        new_flight = self.flight_manager.get_flight(new_flight_id)
        return self.booking_service.modify_booking(booking_id, new_flight, new_seat_id)


def _create_sample_aircraft() -> Aircraft:
    seats = [
        Seat(seat_id="1A", type=SeatType.BUSSINESS, price=6000),
        Seat(seat_id="1B", type=SeatType.BUSSINESS, price=6000),
        Seat(seat_id="2A", type=SeatType.ECONOMY, price=3000),
        Seat(seat_id="2B", type=SeatType.ECONOMY, price=3000),
    ]
    return Aircraft(model="Boeing 737", seats=seats)


def demo() -> None:
    system = AirlineManagementSystem()

    admin = Admin(email="admin@airline.com", name="System Admin", role=UserRole.ADMIN, employee_id="ADM-1")
    crew = Staff(
        email="captain@airline.com",
        name="Captain Jane",
        role=UserRole.STAFF,
        employee_id="EMP-007",
        designation="Pilot",
    )

    flight_1 = Flight(
        flight_number="IN100",
        source="BLR",
        destination="DEL",
        departure_time=datetime.now() + timedelta(days=1),
        arrival_time=datetime.now() + timedelta(days=1, hours=2),
        aircraft=_create_sample_aircraft(),
    )
    flight_2 = Flight(
        flight_number="IN101",
        source="BLR",
        destination="DEL",
        departure_time=datetime.now() + timedelta(days=1, hours=4),
        arrival_time=datetime.now() + timedelta(days=1, hours=6),
        aircraft=_create_sample_aircraft(),
    )

    system.add_flight(flight_1)
    system.add_flight(flight_2)
    system.flight_manager.assign_crew(flight_1.flight_id, crew)
    print(f"Admin {admin.employee_id} added and managed flights.")

    search_criteria = FlightSearchCriteria(source="BLR", destination="DEL", date=(datetime.now() + timedelta(days=1)).date())
    flights = system.search_flights(search_criteria)
    print(f"Found {len(flights)} flight(s) for BLR -> DEL")

    passenger_1 = Passenger(
        email="alice@example.com",
        name="Alice",
        role=UserRole.PASSENGER,
        passport_number="P123456",
        baggage=[Baggage(weight=12.5)],
    )
    passenger_2 = Passenger(
        email="bob@example.com",
        name="Bob",
        role=UserRole.PASSENGER,
        passport_number="P987654",
        baggage=[Baggage(weight=8.0)],
    )

    successful_bookings: List[Booking] = []
    result_lock = threading.Lock()

    def concurrent_booking_attempt(passenger: Passenger) -> None:
        try:
            booking = system.book_flight(passenger, flight_1.flight_id, "1A", PaymentMethod.UPI)
            with result_lock:
                successful_bookings.append(booking)
            print(f"Booking success for {passenger.name}: {booking.booking_id}")
        except Exception as exc:
            print(f"Booking failed for {passenger.name}: {exc}")

    t1 = threading.Thread(target=concurrent_booking_attempt, args=(passenger_1,))
    t2 = threading.Thread(target=concurrent_booking_attempt, args=(passenger_2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    if successful_bookings:
        original_booking = successful_bookings[0]
        modified_booking = system.modify_booking(original_booking.booking_id, flight_2.flight_id, "1B")
        print(
            f"Modified booking {original_booking.booking_id} -> {modified_booking.booking_id} "
            f"on flight {modified_booking.flight.flight_number}"
        )

        cancelled_booking = system.cancel_booking(modified_booking.booking_id)
        print(f"Cancelled booking: {cancelled_booking.booking_id} (refund processed)")


if __name__ == "__main__":
    demo()