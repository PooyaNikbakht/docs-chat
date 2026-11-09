from datetime import date, time

import pytest

from app.booking.catalog import KINGSWAY_SERVICES
from app.models import BookingAction, BookingEvent, ChoicesEvent, TextEvent
from app.receptionist.desk import BookingDesk, DeskError, DeskState
from app.receptionist.intent import (
    find_service,
    format_time,
    is_booking_message,
    is_no,
    is_yes,
    parse_contact,
    parse_day,
    parse_time,
    parse_window,
    times_in,
)
from app.receptionist.offline import OfflineReceptionist
from tests.booking_fakes import SATURDAY, SUNDAY, TODAY, mock_provider, now

# ---- intent parsing (today is Monday, November 9 2026) ----


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("today please", TODAY),
        ("tomorrow morning", date(2026, 11, 10)),
        ("is Saturday open", SATURDAY),
        ("sat afternoon", SATURDAY),
        ("this weekend", SATURDAY),
        ("next monday", date(2026, 11, 16)),
        ("monday", TODAY),
        ("Nov 20", date(2026, 11, 20)),
        ("the 21st", date(2026, 11, 21)),
        ("the 3rd", date(2026, 12, 3)),
        ("2026-12-01", date(2026, 12, 1)),
        ("11/30", date(2026, 11, 30)),
        ("how much is a fade", None),
        ("is it sunny", None),
    ],
)
def test_parse_day(text, expected):
    assert parse_day(text, TODAY) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2pm", time(14, 0)),
        ("at 2:30 PM", time(14, 30)),
        ("14:15", time(14, 15)),
        ("at 3", time(15, 0)),
        ("10 a.m.", time(10, 0)),
        ("after 3pm", None),
        ("on the 21st", None),
    ],
)
def test_parse_time(text, expected):
    assert parse_time(text) == expected


def test_parse_window():
    assert parse_window("saturday morning").label == "in the morning"
    after = parse_window("anything after 4pm?")
    assert after is not None and after.start == 16 * 60
    assert parse_window("Saturday") is None


def test_find_service_prefers_the_specific_one():
    def key(text: str) -> str | None:
        found = find_service(text, KINGSWAY_SERVICES)
        return found.key if found else None

    assert key("a haircut and beard") == "cut-beard"
    assert key("buzz cut for me") == "buzz"
    assert key("cut for my son") == "kids"
    assert key("skin fade") == "fade"
    assert key("just a haircut") == "classic"
    assert key("what are your hours") is None


def test_booking_message_detection():
    services = KINGSWAY_SERVICES
    assert is_booking_message("Can I book something?", services, TODAY)
    assert is_booking_message("Any availability Saturday?", services, TODAY)
    assert is_booking_message("fade on saturday?", services, TODAY)
    assert not is_booking_message("What's your cancellation policy?", services, TODAY)
    assert not is_booking_message("Are you open on Sunday?", services, TODAY)


def test_contact_yes_no_and_times():
    c = parse_contact("Alex Chen, alex@Example.com, 416-555-0100")
    assert (c.name, c.email, c.phone) == ("Alex Chen", "alex@example.com", "416-555-0100")
    assert parse_contact("my name is sam lee and my email is sam@x.io").name == "Sam Lee"
    assert parse_contact("sam@x.io").name is None
    assert is_yes("Yes please") and is_yes("book it") and not is_yes("yesterday")
    assert is_no("no, a different time") and not is_no("now")
    assert times_in("We have 2 PM and 3:30 p.m. open") == {"2:00 PM", "3:30 PM"}
    assert format_time(time(9, 5)) == "9:05 AM"


# ---- the offline flow ----


class Chat:
    def __init__(self, **provider_kwargs) -> None:
        self.provider = mock_provider(**provider_kwargs)
        self.state = DeskState()
        self.bot = OfflineReceptionist("Kingsway Cuts", "(416) 555-0187")

    def desk(self) -> BookingDesk:
        self.state.turn += 1
        return BookingDesk(self.provider, self.state, now)

    async def say(self, text: str) -> list:
        return await self.bot.handle_text(self.desk(), text)

    async def tap(self, kind: str, value: str | None = None) -> list:
        return await self.bot.handle_action(self.desk(), BookingAction(type=kind, id=value))


def text_of(reply: list) -> str:
    return " ".join(e.text for e in reply if isinstance(e, TextEvent))


def one(reply: list, kind: type):
    found = [e for e in reply if isinstance(e, kind)]
    assert len(found) == 1, reply
    return found[0]


async def test_offers_real_open_times_then_books_after_confirmation():
    chat = Chat()
    open_times = await chat.provider.find_slots("kingsway_svc_fade", SATURDAY)

    reply = await chat.say("Is Saturday afternoon open for a skin fade?")
    choices = one(reply, ChoicesEvent)
    assert choices.kind == "slot" and choices.options
    real = {format_time(s.start) for s in open_times}
    assert {o.label for o in choices.options} <= real
    assert times_in(text_of(reply)) <= real  # never a time the system didn't return
    assert text_of(reply).startswith("Yes, we have")
    assert "Want me to book one?" in text_of(reply)

    reply = await chat.tap("slot", choices.options[0].id)
    assert "name and email" in text_of(reply)

    reply = await chat.say("Alex Chen, alex@example.com")
    pending = one(reply, BookingEvent)
    assert pending.status == "pending" and pending.name == "Alex Chen"
    assert chat.provider.bookings == []  # nothing written before the visitor confirms

    reply = await chat.tap("confirm")
    done = one(reply, BookingEvent)
    assert done.status == "confirmed" and done.reference
    assert len(chat.provider.bookings) == 1
    assert "You're booked, Alex" in text_of(reply)


async def test_asks_for_the_service_then_the_day():
    chat = Chat()
    reply = await chat.say("Can I book an appointment?")
    assert one(reply, ChoicesEvent).kind == "service"
    reply = await chat.tap("service", "classic")
    days = one(reply, ChoicesEvent)
    assert days.kind == "day" and len(days.options) == 5
    reply = await chat.tap("day", days.options[0].id)
    assert one(reply, ChoicesEvent).kind == "slot"


async def test_typed_yes_confirms_and_typed_no_reoffers():
    chat = Chat()
    await chat.say("haircut saturday")
    slot_id = next(iter(chat.state.offered))
    await chat.tap("slot", slot_id)
    await chat.say("Sam Lee sam@example.com")
    reply = await chat.say("no, a different time")
    assert chat.state.pending is None and one(reply, ChoicesEvent).kind == "slot"
    assert "nothing is booked" in text_of(reply)

    await chat.tap("slot", one(reply, ChoicesEvent).options[0].id)
    assert chat.state.pending is not None  # details were remembered
    reply = await chat.say("yes please")
    assert one(reply, BookingEvent).status == "confirmed"


async def test_a_specific_time_is_matched_or_the_closest_are_offered():
    chat = Chat(busy_percent=0)
    reply = await chat.say("fade saturday at 2pm")
    assert "name and email" in text_of(reply)
    chat2 = Chat()
    open_times = {
        format_time(s.start) for s in await chat2.provider.find_slots("kingsway_svc_fade", SATURDAY)
    }
    closed = next(
        f"{h}:{m:02d}pm"
        for h in (1, 2, 3, 4)
        for m in (0, 30)
        if format_time(time(h + 12, m)) not in open_times
    )
    reply = await chat2.say(f"fade saturday at {closed}")
    assert "isn't open" in text_of(reply)
    assert {o.label for o in one(reply, ChoicesEvent).options} <= open_times


async def test_no_slots_points_to_the_next_open_day():
    chat = Chat()
    reply = await chat.say("any openings sunday for a hot towel shave?")
    text = text_of(reply)
    assert "nothing open on Sunday" in text and "next opening" in text
    choices = one(reply, ChoicesEvent)
    assert SUNDAY.isoformat().replace("-", "") not in choices.options[0].id


async def test_no_openings_at_all_offers_the_phone_number():
    chat = Chat(busy_percent=100)
    reply = await chat.say("book a fade saturday")
    assert "(416) 555-0187" in text_of(reply)
    assert not [e for e in reply if isinstance(e, ChoicesEvent)]


async def test_slot_just_taken_at_confirmation_reoffers_fresh_times():
    chat = Chat()
    await chat.say("fade saturday")
    slot_id, slot = next(iter(chat.state.offered.items()))
    await chat.tap("slot", slot_id)
    await chat.say("Alex Chen alex@example.com")
    chat.provider.take(slot)  # someone else books it first
    reply = await chat.tap("confirm")
    assert "was just booked by someone else" in text_of(reply)
    assert slot_id not in {o.id for o in one(reply, ChoicesEvent).options}
    assert chat.provider.bookings == [] and chat.state.pending is None


async def test_bad_email_is_asked_again():
    chat = Chat()
    await chat.say("fade saturday")
    await chat.tap("slot", next(iter(chat.state.offered)))
    reply = await chat.say("Alex, alex@example")
    assert "email" in text_of(reply).lower() and chat.state.pending is None


async def test_unknown_or_stale_slot_tap_is_refused():
    chat = Chat()
    await chat.say("fade saturday")
    reply = await chat.tap("slot", "fade-202611141234")
    assert "isn't on offer" in text_of(reply)


async def test_desk_refuses_to_confirm_in_the_same_message_or_unoffered_slots():
    chat = Chat()
    desk = chat.desk()
    avail = await desk.availability(KINGSWAY_SERVICES[3], SATURDAY)
    slot_id = avail.shown[0][0]
    desk.stage(slot_id, "Alex Chen", "alex@example.com")
    with pytest.raises(DeskError) as exc:
        await desk.confirm()
    assert exc.value.code == "not_confirmed_yet"
    with pytest.raises(DeskError) as exc:
        desk.stage("fade-209901010900", "Alex Chen", "alex@example.com")
    assert exc.value.code == "unknown_slot"
    with pytest.raises(DeskError) as exc:
        await desk.availability(KINGSWAY_SERVICES[3], date(2026, 11, 1))
    assert exc.value.code == "past_date"
