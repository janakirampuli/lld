'''
requirements:

1. browse/search concerts by artist, venue, date, time
2. view seating arrangement for a concert
3. select seats -> purchase ticket
4. waitlist for sold-out concerts
5. booking confirmation via email/SMS
6. cancel booking -> seat released -> waitlist notified
7. concurrency: no double booking
8. fair booking: firs-come first serve
9. payment abstracted out behind interface
10. scalable to multiple venues, concerts

core entities:

User
Concert
Venue
Seat
Booking
Ticket
Payment
WailistEntry
SearchCriteria

enums:

BookingStatus
SeatStatus
SeatType
PaymentStatus
PaymentMethod
ConcertStatus
NotificationType

classes and interfaces:

ConcertSearchSerice:
- search(criteria: SearchCriteria) -> list[Concert]
- get_concert_by_id(concert_id) -> Concert

BookingService:
- create_booking(user, concert, seat_ids, payment_method)
- cancel_booking(booking_id)

PaymentProcessor:
- process_payment(amount, method)
- process_refund(payment_id, amount)

SeatManager:
- get_available_seats(concert_id)
- get_seat_map(concert_id)
- lock_seats(concert_id, seat_ids)
- book_seats(concert_id, seat_ids)
- release_seats(concert_id, seat_ids)

WaitlistManager:
- add_to_waitlist(user, concert_id, num_seats, seat_type)
- remove_from_waitlist(entry_id)
- process_waitlist(concert_id, freed_seats)

NotificationService:
- send(user, message, notification_type)

User:
- user_id
- name
- email
- phone
- bookings

Artist:
- artist_id
- name
- genre

Venue:
- venue_id
- name
- location
- capacity
- seat_map

SeatMap:
- sections - e.g. {"GOLD": [Seat, ...], "VIP": [...]}
- get_seats_by_type(seat_type)

Seat:
- seat_id
- seat_number
- section
- status
- price

Concert:
- concert_id
- title
- artist
- venue
- date_time
- status
- seat_map

Booking:
- booking_id
- user
- concert
- tickets
- payment
- status
- booking_time

Ticket:
- ticket_id
- seat
- concert
- price

Payment:
- payment_id
- amount
- method
- status
- transaction_time

WaitlistEntry:
- entry_id
- user
- concert_id
- num_seats
- seat_type
- added_time

SearchCriteria:
- artist_name
- venue_name
- date
- time_range
- seat_type

ConcertBookingSystem:
- main entry point
- manages concert_search_service, booking_service, seat_manager, waitlist_manager, notification_servive
- singleton

ConcertManager:
- add_concert(concert)
- cancel_concert(concert_id)
- get_all_concerts()
- concerts

BookingserviceImpl:
- lock seats -> calculate total -> process payment -> confirm booking -> notify
- on failure -> release seats -> return error
- on cancel -> release seats -> process refund -> waitlist_manager.process_waitlist() -> notify
- bookings

SeatManagerImpl:
- concert_seats - {concert_id: {seat_id: Seat}}
- use Threading.Lock per (concert_id, seat_id)

WaitlistManagerImpl:
- waitlists - {concert_id: [entries]}
- process_waitlist()


'''

import threading
from enum import Enum
from typing import List, Dict
import uuid

class SeatStatus(Enum):
    FREE = 0
    BLOCKED = 1
    BOOKED = 2

class SeatType(Enum):
    REGULAR = 0
    GOLD = 1
    VIP = 2

class Seat:
    def __init__(self, id: int, price: int, seat_type: SeatType):
        self.id = id
        self.price = price
        self.status: SeatStatus = SeatStatus.FREE
        self.seat_type: SeatType = seat_type
        self.lock = threading.Lock()
    
    def block(self):
        with self.lock:
            if self.status == SeatStatus.FREE:
                self.status = SeatStatus.BLOCKED
                print(f"seat {self.id} blocked")
            else:
                print(f"seat is not free to block")

    def book(self):
        with self.lock:
            if self.status == SeatStatus.BLOCKED:
                self.status = SeatStatus.BOOKED
                print(f"seat {self.id} booked")
            else:
                print(f"seat booked already")
    
    def release(self):
        with self.lock:
            if self.status == SeatStatus.BOOKED:
                self.status = SeatStatus.FREE

class Concert:
    def __init__(self, id: str, artist: str, venue: str):
        self.id = id
        self.artist = artist
        self.venue = venue
        self.seats: List[Seat] = []

    def add_seats(self, seat: Seat):
        self.seats.append(seat)

class User:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

class BookingStatus(Enum):
    PENDING = 0
    CONFIRMED = 1
    CANCELLED = 2

class Booking:
    def __init__(self, user: User, concert: Concert, seats: List[Seat]):
        self.id = str(uuid.uuid4())
        self.user = user
        self.concert = concert
        self.seats = seats
        self.price = 0
        for seat in self.seats:
            self.price += seat.price
        self.booking_status = BookingStatus.PENDING

    def confirm_booking(self):
        if self.booking_status == BookingStatus.PENDING:
            self.booking_status = BookingStatus.CONFIRMED
            # send notif
            print(f"sending notif of booking")

    def cancel_booking(self):
        if self.booking_status == BookingStatus.CONFIRMED:
            self.booking_status = BookingStatus.CANCELLED
            for seat in self.seats:
                seat.release()
            print(f"booking {self.id} cancelled")

class ConcertBookingSystem:
    instance = None
    lock = threading.Lock()

    def __new__(cls):
        if cls.instance is None:
            with cls.lock:
                if cls.instance is None:
                    cls.instance = super(ConcertBookingSystem, cls).__new__(cls)
                    cls.instance.initialize()
        return cls.instance
    
    def initialize(self):
        self.concerts: Dict[str, Concert] = {}
        self.bookings: Dict[str, Booking] = {}

    def add_concert(self, concert: Concert):
        self.concerts[concert.id] = concert

    def search_concert(self, id: int):
        return self.concerts.get(id)
    
    def book_ticket(self, concert: Concert, user: User, seats: List[Seat]):
        with self.lock:
            for seat in seats:
                if seat.status != SeatStatus.FREE:
                    print(f"seat not available")
                    return
            for seat in seats:
                seat.block()
            
            booking = Booking(user, concert, seats)
            self.bookings[booking.id] = booking
            self.process_payment(booking)
            booking.confirm_booking()
            for seat in seats:
                seat.book()
            print(f"booking {booking.id} - {len(booking.seats)} booked for {booking.price}")
        
        return booking
    
    def cancel_booking(self, booking_id: str):
        booking = self.bookings.get(booking_id)
        if booking:
            booking.cancel_booking()
            print(f"booking {booking.id} - {len(booking.seats)} cancelled")
            del self.bookings[booking_id]

    def process_payment(self, booking: Booking):
        print(f"payment done")

def demo():
    cbs = ConcertBookingSystem()
    c1 = Concert("1", "taylor", "blr")
    seat = {}
    for i in range(10):
        if i < 5:
            seat[i] = Seat(i, 100, SeatType.REGULAR)
            c1.add_seats(seat)
        else:
            seat[i] = Seat(i, 500, SeatType.GOLD)
            c1.add_seats(seat)

    cbs.add_concert(concert=c1)

    u1 = User(1, "janaki", "foo@gmail.com")

    cbs.book_ticket(c1, u1, [seat[0], seat[1]])

    c2 = Concert("2", "ed", "hyd")


if __name__ == "__main__":
    demo()