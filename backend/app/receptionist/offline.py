"""The offline receptionist: a deterministic booking conversation with no model and no key.

It reads the day, time, service and contact details with small parsers, calls the same
booking desk the Claude tools use, and always asks the visitor to confirm before booking.
It also handles every widget tap (service, day, time, confirm, change), whichever provider
is active, since a tap needs no language understanding.
"""

from datetime import date, time

from app.booking.base import BookingError, Service, Slot, SlotTakenError
from app.models import BookingAction, BookingEvent, ChoicesEvent, TextEvent
from app.receptionist.desk import Availability, BookingDesk, DeskError
from app.receptionist.intent import (
    Window,
    day_label,
    find_service,
    format_time,
    is_no,
    is_yes,
    parse_contact,
    parse_day,
    parse_iso,
    parse_time,
    parse_window,
)

Reply = list[TextEvent | ChoicesEvent | BookingEvent]


def on_day(day: date, today: date) -> str:
    label = day_label(day, today)
    return label if label in ("today", "tomorrow") else f"on {label}"


def join_times(labels: list[str]) -> str:
    if len(labels) <= 1:
        return "".join(labels)
    return ", ".join(labels[:-1]) + f" and {labels[-1]}"


class OfflineReceptionist:
    def __init__(self, business: str, phone: str) -> None:
        self.business = business
        self.phone = phone

    # ---- entry points ----

    async def handle_action(self, desk: BookingDesk, action: BookingAction) -> Reply:
        desk.state.last_booking_turn = desk.state.turn
        state = desk.state
        if action.type == "service":
            service = desk.service_by_key_or_id(action.id or "")
            if service is None:
                return [TextEvent(text="Sorry, I don't know that service."), desk.service_choices()]
            state.service_id = service.id
            if state.day:
                return await self.offer(desk, service, state.day, state.window)
            return await self.ask_day(desk, service, f"A {service.name.lower()} it is.")
        if action.type == "day":
            day = parse_iso(action.id)
            if day is None:
                return [TextEvent(text="Sorry, I couldn't read that day.")]
            service = desk.service(state.service_id)
            if service is None:
                state.day = day
                return self.ask_service(desk, f"Happy to check {day_label(day, desk.today)}.")
            return await self.offer(desk, service, day, None)
        if action.type == "slot":
            slot = desk.offered(action.id or "")
            if slot is None:
                service = desk.service(state.service_id)
                text = "That time isn't on offer anymore."
                if service and state.day:
                    return await self.offer(desk, service, state.day, None, lead=text)
                return [TextEvent(text=text + " Which day would you like?")]
            return self.choose(desk, action.id or "", slot)
        if action.type == "confirm":
            return await self.confirm(desk)
        return await self.change(desk)

    async def handle_text(self, desk: BookingDesk, text: str) -> Reply:
        state = desk.state
        state.last_booking_turn = state.turn
        today = desk.today
        day = parse_day(text, today)
        clock = parse_time(text)
        window = parse_window(text)
        service = find_service(text, desk.catalog.services)
        new_request = bool(day or clock or window or service)

        if state.pending and not new_request:
            if is_yes(text):
                return await self.confirm(desk)
            if is_no(text):
                return await self.change(desk)
            details = parse_contact(text)
            if details.email or details.phone:
                return self.collect(desk, state.pending.slot_id, text)
            return [
                TextEvent(
                    text="Shall I book it? Tap Book it to confirm, or tell me what to change."
                ),
                desk.pending_event(),
            ]

        if state.chosen and not new_request:
            return self.collect(desk, state.chosen, text)

        if new_request and state.pending:
            desk.drop_pending()
        if service:
            state.service_id = service.id
        service = service or desk.service(state.service_id)
        if clock and not day:
            day = state.day
        if not service:
            if day:
                state.day = day
            state.window = window or state.window
            lead = f"Happy to check {day_label(day, today)}." if day else "Happy to help you book."
            return self.ask_service(desk, lead)
        day = day or state.day
        if day is None:
            state.window = window
            return await self.ask_day(desk, service, "Sure.")
        if clock:
            return await self.pick_time(desk, service, day, clock)
        return await self.offer(desk, service, day, window)

    # ---- steps ----

    def ask_service(self, desk: BookingDesk, lead: str) -> Reply:
        return [TextEvent(text=f"{lead} Which service would you like?"), desk.service_choices()]

    async def ask_day(self, desk: BookingDesk, service: Service, lead: str) -> Reply:
        choices = await desk.day_choices(service)
        if not choices.options:
            return self.no_openings(service)
        return [TextEvent(text=f"{lead} Which day works for you?"), choices]

    def no_openings(self, service: Service) -> Reply:
        return [
            TextEvent(
                text=(
                    f"I couldn't find any open times for a {service.name.lower()} in the next "
                    f"two weeks. Please call us at {self.phone} and we'll find you a spot."
                )
            )
        ]

    async def offer(
        self,
        desk: BookingDesk,
        service: Service,
        day: date,
        window: Window | None,
        *,
        lead: str = "",
    ) -> Reply:
        try:
            avail = await desk.availability(service, day, window)
        except DeskError as exc:
            return [TextEvent(text=_join(lead, f"{exc.message} Which day would you like?"))]
        return self.describe(desk, avail, lead)

    def describe(self, desk: BookingDesk, avail: Availability, lead: str = "") -> Reply:
        today = desk.today
        name = avail.service.name.lower()
        when = on_day(avail.day, today)
        if avail.slots:
            labels = [format_time(s.start) for _, s in avail.shown]
            if avail.window_empty and avail.window:
                text = (
                    f"Nothing is open {avail.window.label} {when}, but we have "
                    f"{_summary(labels, len(avail.slots))}."
                )
            elif len(avail.slots) <= 3:
                text = f"Yes, we have {join_times(labels)} open {when} for a {name}."
            else:
                window = avail.window
                in_window = [s for s in avail.slots if window is None or window.contains(s.start)]
                where = f" {window.label}" if window else ""
                count = f"{len(in_window)} open times" if len(in_window) > 1 else "one open time"
                text = f"Yes, we have {count} {when}{where} for a {name}"
                text += (
                    f": {join_times(labels[:3])}."
                    if len(in_window) <= 3
                    else (f". Here are a few: {join_times(labels[:3])}.")
                )
            reply: Reply = [TextEvent(text=_join(lead, text + " Want me to book one?"))]
            reply.append(desk.slot_choices(avail.day, avail.shown))
            return reply
        if avail.next_day:
            labels = [format_time(s.start) for _, s in avail.next_shown[:3]]
            text = (
                f"Sorry, there's nothing open {when} for a {name}. The next opening is "
                f"{on_day(avail.next_day, today)}, with {join_times(labels)} free. "
                "Want one of those?"
            )
            return [
                TextEvent(text=_join(lead, text)),
                desk.slot_choices(avail.next_day, avail.next_shown),
            ]
        return self.no_openings(avail.service)

    async def pick_time(self, desk: BookingDesk, service: Service, day: date, clock: time) -> Reply:
        try:
            avail = await desk.availability(service, day, None)
        except DeskError as exc:
            return [TextEvent(text=f"{exc.message} Which day would you like?")]
        exact = next(
            (
                s
                for s in avail.slots
                if (s.start.hour, s.start.minute) == (clock.hour, clock.minute)
            ),
            None,
        )
        if exact:
            slot_id = desk.slot_id(exact)
            desk.state.remember(slot_id, exact)
            return self.choose(desk, slot_id, exact)
        if not avail.slots:
            return self.describe(desk, avail)
        # Offer the times closest to the one they asked for.
        target = clock.hour * 60 + clock.minute
        nearest = sorted(
            avail.slots, key=lambda s: abs(s.start.hour * 60 + s.start.minute - target)
        )[:4]
        nearest.sort(key=lambda s: s.start)
        shown = []
        for slot in nearest:
            sid = desk.slot_id(slot)
            desk.state.remember(sid, slot)
            shown.append((sid, slot))
        labels = [format_time(s.start) for _, s in shown]
        text = (
            f"{format_time(clock)} isn't open {on_day(day, desk.today)}. "
            f"The closest times are {join_times(labels)}. Want one of those?"
        )
        return [TextEvent(text=text), desk.slot_choices(day, shown)]

    def choose(self, desk: BookingDesk, slot_id: str, slot: Slot) -> Reply:
        state = desk.state
        state.chosen = slot_id
        if state.name and state.email:
            event = desk.stage(slot_id, state.name, state.email, state.phone or "")
            return [
                TextEvent(text="Here's what I'll book, under the same details. Shall I go ahead?"),
                event,
            ]
        service = desk.service(slot.service_id)
        what = service.name.lower() if service else "appointment"
        return [
            TextEvent(
                text=(
                    f"Good choice: a {what} {desk.describe(slot)}. What name and email "
                    "should I put the booking under? A phone number is optional."
                )
            )
        ]

    def collect(self, desk: BookingDesk, slot_id: str, text: str) -> Reply:
        state = desk.state
        details = parse_contact(text)
        has_contact = bool(details.email or details.phone)
        name = details.name if (details.name and (has_contact or not state.name)) else state.name
        email = details.email or state.email
        phone = details.phone or state.phone
        state.name, state.email, state.phone = name, email, phone
        if not name and not email:
            return [
                TextEvent(
                    text="What name and email should I put the booking under? For example: "
                    "Sam Lee, sam@example.com"
                )
            ]
        if not email:
            first = name.split()[0] if name else "there"
            return [
                TextEvent(text=f"Thanks, {first}. What email should I send the confirmation to?")
            ]
        if not name:
            return [TextEvent(text="Thanks. And what name should I put the booking under?")]
        try:
            event = desk.stage(slot_id, name, email, phone or "")
        except DeskError as exc:
            if exc.code == "invalid_details":
                state.email = None if "email" in exc.message.lower() else state.email
                return [TextEvent(text=f"{exc.message}. Could you send it again?")]
            state.chosen = None
            return [TextEvent(text=exc.message)]
        return [
            TextEvent(text="Here's what I'll book. Shall I go ahead?"),
            event,
        ]

    async def confirm(self, desk: BookingDesk) -> Reply:
        pending = desk.state.pending
        try:
            booking, event = await desk.confirm()
        except SlotTakenError:
            assert pending is not None
            service = desk.service(pending.slot.service_id)
            lead = f"Sorry, {format_time(pending.slot.start)} was just booked by someone else."
            if service is None:
                return [TextEvent(text=lead)]
            avail = await desk.availability(service, pending.slot.start.date(), None)
            if avail.slots:
                labels = [format_time(s.start) for _, s in avail.shown]
                return [
                    TextEvent(
                        text=f"{lead} Still open {on_day(avail.day, desk.today)}: "
                        f"{join_times(labels[:3])}. Want one of those?"
                    ),
                    desk.slot_choices(avail.day, avail.shown),
                ]
            return self.describe(desk, avail, lead)
        except DeskError as exc:
            if exc.code == "nothing_pending":
                return [
                    TextEvent(text="There's nothing waiting to book yet. Which day would you like?")
                ]
            return [TextEvent(text=exc.message)]
        except BookingError as exc:
            if pending:
                desk.state.pending = pending
            return [TextEvent(text=f"I couldn't book that: {exc.message}"), desk.pending_event()]
        first = booking.customer.name.split()[0]
        staff = f" with {booking.staff.name}" if booking.staff else ""
        text = (
            f"You're booked, {first}: {booking.service.name.lower()}{staff} "
            f"{desk.describe(booking.slot)}. Your reference is {booking.reference}. See you then!"
        )
        return [TextEvent(text=text), event]

    async def change(self, desk: BookingDesk) -> Reply:
        pending = desk.drop_pending()
        desk.state.chosen = None
        if pending is None:
            return [TextEvent(text="No problem. Which day would you like instead?")]
        service = desk.service(pending.slot.service_id)
        if service is None:
            return [TextEvent(text="No problem. Which day would you like instead?")]
        return await self.offer(
            desk, service, pending.slot.start.date(), None, lead="No problem, nothing is booked."
        )


def _summary(labels: list[str], total: int) -> str:
    if total <= 3:
        return join_times(labels)
    return f"{join_times(labels[:3])} and a few more"


def _join(lead: str, text: str) -> str:
    return f"{lead} {text}" if lead else text
