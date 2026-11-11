"""The booking interface: services, open slots and bookings, whatever system holds them.

The receptionist only talks to a `BookingProvider`. Two adapters ship: an HTTP adapter for
the business's real booking system, and an in-memory mock with a weekly schedule, used by
the tests and the offline demo.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Service:
    id: str
    key: str  # short name used in slot ids, such as "fade"
    name: str
    duration_min: int
    price_cents: int
    description: str = ""
    # Lower-case phrases a visitor might use for this service, most specific first.
    keywords: tuple[str, ...] = ()

    @property
    def price(self) -> str:
        dollars, cents = divmod(self.price_cents, 100)
        return f"${dollars}" if cents == 0 else f"${dollars}.{cents:02d}"


@dataclass(frozen=True)
class Staff:
    id: str
    name: str


@dataclass(frozen=True)
class Slot:
    """An open start time for one service. `staff_ids` are the people free at that time."""

    service_id: str
    start: datetime  # timezone-aware, in the business's timezone
    staff_ids: tuple[str, ...] = ()

    @property
    def start_ms(self) -> int:
        return int(self.start.timestamp() * 1000)


@dataclass(frozen=True)
class Customer:
    name: str
    email: str
    phone: str = ""


@dataclass(frozen=True)
class Booking:
    reference: str
    service: Service
    slot: Slot
    staff: Staff | None
    customer: Customer
    # A deposit is due: the time is held while the visitor pays at this Stripe Checkout link.
    payment_url: str | None = None
    deposit_cents: int = 0

    @property
    def deposit(self) -> str:
        dollars, cents = divmod(self.deposit_cents, 100)
        return f"${dollars}" if cents == 0 else f"${dollars}.{cents:02d}"


@dataclass(frozen=True)
class Catalog:
    """What the business offers: its services, its staff and its timezone."""

    timezone: ZoneInfo
    services: tuple[Service, ...]
    staff: tuple[Staff, ...] = field(default_factory=tuple)

    def service(self, service_id: str) -> Service | None:
        return next((s for s in self.services if s.id == service_id), None)

    def staff_member(self, staff_id: str) -> Staff | None:
        return next((s for s in self.staff if s.id == staff_id), None)


class BookingError(Exception):
    """A booking failed in a way the visitor should hear about."""

    code = "booking_failed"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class SlotTakenError(BookingError):
    """Someone else booked the time between the offer and the confirmation."""

    code = "slot_taken"


class BookingUnavailableError(BookingError):
    """The booking system can't be reached or answered with an unexpected error."""

    code = "booking_unavailable"


class BookingProvider(Protocol):
    catalog: Catalog

    async def find_slots(self, service_id: str, day: date) -> list[Slot]:
        """Open start times for `service_id` on `day` (in the business's timezone), in order."""
        ...

    async def book(self, slot: Slot, customer: Customer, notes: str = "") -> Booking:
        """Book `slot`. Raises `SlotTakenError` if it is no longer open."""
        ...
