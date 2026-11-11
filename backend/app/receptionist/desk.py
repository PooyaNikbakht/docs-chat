"""The booking desk: the one place that reads availability and writes bookings.

Both receptionists (Claude with tools, and the offline one) go through it, so the rules
hold whichever is answering:

- Times are only ever offered from the booking provider, and only offered times can be booked.
- A booking is staged first and written only on a later message, after the visitor confirms.
- Details are validated before anything reaches the booking system.
"""

import re
import threading
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.booking.base import Booking, BookingProvider, Customer, Service, Slot, SlotTakenError
from app.models import BookingEvent, ChoiceOption, ChoicesEvent
from app.receptionist.intent import EMAIL_RE, Window, day_label, format_time, short_day

MAX_SHOWN = 6
MAX_DAYS_AHEAD = 60
NEXT_OPENING_SEARCH_DAYS = 14


@dataclass
class Pending:
    slot_id: str
    slot: Slot
    customer: Customer
    turn: int


@dataclass
class DeskState:
    """What the receptionist remembers for one visitor's conversation."""

    turn: int = 0
    service_id: str | None = None
    day: date | None = None
    window: Window | None = None
    offered: dict[str, Slot] = field(default_factory=dict)
    chosen: str | None = None  # a slot id waiting for the visitor's details
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    pending: Pending | None = None
    last_booking_turn: int = -10
    booked: list[str] = field(default_factory=list)

    @property
    def in_flow(self) -> bool:
        """True while a booking conversation is under way."""
        recent = self.turn - self.last_booking_turn <= 1
        return self.chosen is not None or self.pending is not None or recent

    def remember(self, slot_id: str, slot: Slot) -> None:
        self.offered[slot_id] = slot
        while len(self.offered) > 60:
            self.offered.pop(next(iter(self.offered)))


class DeskStore:
    """Desk state per (bot, session), in memory with a size cap."""

    def __init__(self, max_sessions: int = 2000) -> None:
        self.max_sessions = max_sessions
        self._states: OrderedDict[tuple[str, str], DeskState] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, bot_id: str, session_id: str) -> DeskState:
        with self._lock:
            key = (bot_id, session_id)
            state = self._states.get(key) or DeskState()
            self._states[key] = state
            self._states.move_to_end(key)
            while len(self._states) > self.max_sessions:
                self._states.popitem(last=False)
            return state


class DeskError(Exception):
    """The visitor or the model asked for something the desk can't do. Safe to show."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(max_length=120)
    phone: str = Field(default="", max_length=30)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = " ".join(v.split())
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Please give a name")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.fullmatch(v):
            raise ValueError("That email address doesn't look right")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = " ".join(v.split())
        if v and not re.fullmatch(r"[0-9+().\-\s]{7,30}", v):
            raise ValueError("Use digits, spaces and + ( ) - only for the phone number")
        return v


@dataclass
class Availability:
    service: Service
    day: date
    slots: list[Slot]  # every open time that day
    shown: list[tuple[str, Slot]]  # what we offer, with slot ids
    window: Window | None
    next_day: date | None = None
    next_shown: list[tuple[str, Slot]] = field(default_factory=list)

    @property
    def window_empty(self) -> bool:
        """The day has openings, just none in the part of the day the visitor asked for."""
        return (
            bool(self.slots)
            and self.window is not None
            and not any(self.window.contains(s.start) for s in self.slots)
        )


class BookingDesk:
    def __init__(
        self,
        provider: BookingProvider,
        state: DeskState,
        now: Callable[[], datetime],
    ) -> None:
        self.provider = provider
        self.catalog = provider.catalog
        self.state = state
        self._now = now

    @property
    def today(self) -> date:
        return self._now().astimezone(self.catalog.timezone).date()

    # ---- services and days ----

    def service(self, service_id: str | None) -> Service | None:
        return self.catalog.service(service_id) if service_id else None

    def service_by_key_or_id(self, value: str) -> Service | None:
        return next((s for s in self.catalog.services if value in (s.id, s.key)), None)

    def service_choices(self) -> ChoicesEvent:
        # Show the menu in a familiar order: the plain haircut first.
        ordered = sorted(self.catalog.services, key=lambda s: (s.key != "classic", s.price_cents))
        return ChoicesEvent(
            kind="service",
            label="Services",
            options=[
                ChoiceOption(id=s.key, label=s.name, detail=f"{s.price}, {s.duration_min} min")
                for s in ordered
            ],
        )

    async def day_choices(self, service: Service, count: int = 5) -> ChoicesEvent:
        options: list[ChoiceOption] = []
        day = self.today
        for _ in range(NEXT_OPENING_SEARCH_DAYS):
            slots = await self.provider.find_slots(service.id, day)
            if slots:
                options.append(
                    ChoiceOption(
                        id=day.isoformat(),
                        label=short_day(day),
                        detail=f"{len(slots)} open",
                    )
                )
                if len(options) == count:
                    break
            day += timedelta(days=1)
        return ChoicesEvent(
            kind="day", label=f"Days with openings for a {service.name.lower()}", options=options
        )

    def check_day(self, day: date) -> None:
        if day < self.today:
            raise DeskError("past_date", "That day has already passed.")
        if day > self.today + timedelta(days=MAX_DAYS_AHEAD):
            raise DeskError("too_far", "We only take bookings up to two months ahead.")

    # ---- availability ----

    async def availability(
        self, service: Service, day: date, window: Window | None = None
    ) -> Availability:
        self.check_day(day)
        slots = await self.provider.find_slots(service.id, day)
        result = Availability(service, day, slots, self._offer(slots, window), window)
        if not slots:
            nxt = day + timedelta(days=1)
            for _ in range(NEXT_OPENING_SEARCH_DAYS):
                later = await self.provider.find_slots(service.id, nxt)
                if later:
                    result.next_day = nxt
                    result.next_shown = self._offer(later, window)
                    break
                nxt += timedelta(days=1)
        self.state.service_id, self.state.day, self.state.window = service.id, day, window
        return result

    def _offer(self, slots: list[Slot], window: Window | None) -> list[tuple[str, Slot]]:
        """Up to six slots, inside the window when one is set, spread across the day."""
        pool = [s for s in slots if window is None or window.contains(s.start)] or slots
        if len(pool) > MAX_SHOWN:
            step = (len(pool) - 1) / (MAX_SHOWN - 1)
            pool = [pool[round(i * step)] for i in range(MAX_SHOWN)]
        shown = []
        for slot in pool:
            slot_id = self.slot_id(slot)
            self.state.remember(slot_id, slot)
            shown.append((slot_id, slot))
        return shown

    def slot_id(self, slot: Slot) -> str:
        service = self.catalog.service(slot.service_id)
        key = service.key if service else "slot"
        return f"{key}-{slot.start.strftime('%Y%m%d%H%M')}"

    def slot_choices(self, day: date, shown: list[tuple[str, Slot]]) -> ChoicesEvent:
        return ChoicesEvent(
            kind="slot",
            label=f"Open times, {short_day(day)}",
            options=[ChoiceOption(id=sid, label=format_time(s.start)) for sid, s in shown],
        )

    def offered(self, slot_id: str) -> Slot | None:
        return self.state.offered.get(slot_id)

    def describe(self, slot: Slot) -> str:
        """ "on Saturday at 2:30 PM", or "tomorrow at 9:00 AM"."""
        label = day_label(slot.start.date(), self.today)
        when = label if label in ("today", "tomorrow") else f"on {label}"
        return f"{when} at {format_time(slot.start)}"

    def staff_name(self, slot: Slot) -> str | None:
        if len(slot.staff_ids) != 1:
            return None
        member = self.catalog.staff_member(slot.staff_ids[0])
        return member.name if member else None

    # ---- staging and confirming ----

    def stage(self, slot_id: str, name: str, email: str, phone: str = "") -> BookingEvent:
        """Hold the visitor's choice and details until they confirm. Nothing is written yet."""
        slot = self.offered(slot_id)
        if slot is None:
            raise DeskError(
                "unknown_slot", "That time wasn't one of the open times offered. Check again."
            )
        try:
            details = CustomerIn(name=name, email=email, phone=phone)
        except ValidationError as exc:
            first = exc.errors()[0]
            raise DeskError("invalid_details", str(first.get("msg", "Check the details."))) from exc
        customer = Customer(details.name, details.email, details.phone)
        self.state.pending = Pending(slot_id, slot, customer, self.state.turn)
        self.state.chosen = None
        self.state.name, self.state.email = details.name, details.email
        self.state.phone = details.phone or self.state.phone
        return self.pending_event()

    def pending_event(self) -> BookingEvent:
        pending = self.state.pending
        assert pending is not None
        service = self.catalog.service(pending.slot.service_id)
        return BookingEvent(
            status="pending",
            service=service.name if service else "Appointment",
            when=self._full_when(pending.slot),
            staff=self.staff_name(pending.slot),
            name=pending.customer.name,
            contact=pending.customer.email,
            price=service.price if service else None,
        )

    def _full_when(self, slot: Slot) -> str:
        d = slot.start.date()
        return f"{short_day(d)}, {format_time(slot.start)}"

    async def confirm(self) -> tuple[Booking, BookingEvent]:
        """Write the staged booking. Only allowed on a message after the one that staged it."""
        pending = self.state.pending
        if pending is None:
            raise DeskError("nothing_pending", "There's no booking waiting for confirmation.")
        if pending.turn >= self.state.turn:
            raise DeskError(
                "not_confirmed_yet",
                "The visitor hasn't confirmed yet. Show them the details and wait for a yes.",
            )
        try:
            booking = await self.provider.book(pending.slot, pending.customer)
        except SlotTakenError:
            # The time is gone: forget it so it can't be offered or staged again.
            self.state.pending = None
            self.state.offered.pop(pending.slot_id, None)
            raise
        self.state.pending = None
        self.state.offered.pop(pending.slot_id, None)
        self.state.booked.append(booking.reference)
        event = BookingEvent(
            status="awaiting_payment" if booking.payment_url else "confirmed",
            service=booking.service.name,
            when=self._full_when(booking.slot),
            staff=booking.staff.name if booking.staff else None,
            name=booking.customer.name,
            contact=booking.customer.email,
            price=booking.service.price,
            reference=booking.reference,
            payment_url=booking.payment_url,
            deposit=booking.deposit if booking.payment_url else None,
        )
        return booking, event

    def drop_pending(self) -> Pending | None:
        pending, self.state.pending = self.state.pending, None
        return pending
