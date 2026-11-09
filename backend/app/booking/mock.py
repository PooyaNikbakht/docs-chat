"""An in-memory booking system with a realistic week, for tests and the offline demo.

Each barber works set hours with a break. About two thirds of the half-hour blocks are
already taken, chosen by a stable hash of the barber, date and time, so the same day always
shows the same openings and nothing depends on a database or another app.
"""

import hashlib
import secrets
import time
from collections.abc import Callable, Iterable
from datetime import date, datetime, timedelta, tzinfo

from app.booking.base import (
    Booking,
    BookingError,
    Catalog,
    Customer,
    Slot,
    SlotTakenError,
)
from app.booking.catalog import KINGSWAY, KINGSWAY_WEEK, Barber

STEP_MIN = 30
LEAD_MIN = 60  # no bookings that start within the next hour

Clock = Callable[[], float]


class MockBookingProvider:
    def __init__(
        self,
        catalog: Catalog = KINGSWAY,
        week: Iterable[Barber] = KINGSWAY_WEEK,
        *,
        busy_percent: int = 65,
        clock: Clock = time.time,
        seed: str = "demo",
    ) -> None:
        self.catalog = catalog
        self.week = tuple(week)
        self.busy_percent = busy_percent
        self.clock = clock
        self.seed = seed
        # (staff_id, start) -> booked minutes, for bookings made through this provider.
        self._taken: dict[tuple[str, datetime], int] = {}
        self.bookings: list[Booking] = []

    # ---- reading ----

    async def find_slots(self, service_id: str, day: date) -> list[Slot]:
        service = self.catalog.service(service_id)
        if service is None:
            raise BookingError("That service doesn't exist.")
        earliest = datetime.fromtimestamp(self.clock(), self.catalog.timezone) + timedelta(
            minutes=LEAD_MIN
        )
        by_start: dict[datetime, list[str]] = {}
        for barber in self.week:
            if service.key not in barber.services:
                continue
            for start in self._starts(barber, day, service.duration_min):
                if start >= earliest:
                    by_start.setdefault(start, []).append(barber.staff_id)
        return [
            Slot(service_id=service.id, start=start, staff_ids=tuple(staff))
            for start, staff in sorted(by_start.items())
        ]

    def _starts(self, barber: Barber, day: date, minutes: int) -> list[datetime]:
        tz = self.catalog.timezone
        out: list[datetime] = []
        for shift in barber.shifts:
            if shift.weekday != day.weekday():
                continue
            begin = _at(day, shift.start, tz)
            end = _at(day, shift.end, tz)
            brk = (
                (_at(day, shift.break_start, tz), _at(day, shift.break_end, tz))
                if shift.break_start and shift.break_end
                else None
            )
            t = begin
            while t + timedelta(minutes=minutes) <= end:
                finish = t + timedelta(minutes=minutes)
                overlaps_break = brk is not None and t < brk[1] and finish > brk[0]
                if not overlaps_break and self._free(barber.staff_id, t, finish):
                    out.append(t)
                t += timedelta(minutes=STEP_MIN)
        return out

    def _free(self, staff_id: str, start: datetime, end: datetime) -> bool:
        t = start
        while t < end:
            if self._pre_booked(staff_id, t):
                return False
            t += timedelta(minutes=STEP_MIN)
        for (sid, booked_start), minutes in self._taken.items():
            if sid != staff_id:
                continue
            booked_end = booked_start + timedelta(minutes=minutes)
            if start < booked_end and end > booked_start:
                return False
        return True

    def _pre_booked(self, staff_id: str, t: datetime) -> bool:
        key = f"{self.seed}|{staff_id}|{t.strftime('%Y-%m-%d %H:%M')}".encode()
        bucket = int.from_bytes(hashlib.sha256(key).digest()[:2], "big") % 100
        return bucket < self.busy_percent

    # ---- writing ----

    async def book(self, slot: Slot, customer: Customer, notes: str = "") -> Booking:
        service = self.catalog.service(slot.service_id)
        if service is None:
            raise BookingError("That service doesn't exist.")
        open_now = await self.find_slots(service.id, slot.start.date())
        match = next((s for s in open_now if s.start == slot.start), None)
        free = [sid for sid in slot.staff_ids if match and sid in match.staff_ids]
        if match is None or (slot.staff_ids and not free):
            raise SlotTakenError("That time was just booked by someone else.")
        staff_id = (free or list(match.staff_ids))[0]
        self._taken[(staff_id, slot.start)] = service.duration_min
        booking = Booking(
            reference=f"KC-{secrets.token_hex(3).upper()}",
            service=service,
            slot=Slot(service.id, slot.start, (staff_id,)),
            staff=self.catalog.staff_member(staff_id),
            customer=customer,
        )
        self.bookings.append(booking)
        return booking

    def take(self, slot: Slot) -> None:
        """Mark a slot as booked by someone else (for tests and demos of a lost race)."""
        service = self.catalog.service(slot.service_id)
        minutes = service.duration_min if service else STEP_MIN
        for staff_id in slot.staff_ids:
            self._taken[(staff_id, slot.start)] = minutes


def _at(day: date, hhmm: str, tz: tzinfo) -> datetime:
    hours, minutes = (int(x) for x in hhmm.split(":"))
    return datetime(day.year, day.month, day.day, hours, minutes, tzinfo=tz)
