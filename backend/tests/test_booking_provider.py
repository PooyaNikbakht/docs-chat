import json
from datetime import datetime, timedelta

import httpx
import pytest

from app.booking import build_booking_provider
from app.booking.base import (
    BookingError,
    BookingUnavailableError,
    Customer,
    Slot,
    SlotTakenError,
)
from app.booking.catalog import KINGSWAY
from app.booking.http import HttpBookingProvider
from app.booking.mock import MockBookingProvider
from tests.booking_fakes import NOW, SATURDAY, SUNDAY, TODAY, TZ, mock_provider
from tests.conftest import make_settings

FADE = "kingsway_svc_fade"
SHAVE = "kingsway_svc_shave"
CLASSIC = "kingsway_svc_classic"
ALEX = Customer("Alex Chen", "alex@example.com", "416 555 0100")

# ---- mock adapter ----


async def test_mock_slots_fall_inside_working_hours_and_are_sorted():
    slots = await mock_provider().find_slots(FADE, SATURDAY)
    assert slots, "a Saturday should have some openings"
    starts = [s.start for s in slots]
    assert starts == sorted(starts)
    for s in slots:
        assert s.start.tzinfo is not None and s.start.date() == SATURDAY
        # On Saturdays the barbers who do fades work between 9:00 and 19:00.
        assert s.start.hour >= 9 and s.start + timedelta(minutes=45) <= s.start.replace(hour=19)
        assert s.staff_ids and "kingsway_stf_theo" not in s.staff_ids  # Theo doesn't do fades


async def test_mock_schedule_is_stable_and_partly_booked():
    a = await mock_provider().find_slots(CLASSIC, SATURDAY)
    b = await mock_provider().find_slots(CLASSIC, SATURDAY)
    assert a == b
    everything = await mock_provider(busy_percent=0).find_slots(CLASSIC, SATURDAY)
    assert 0 < len(a) < len(everything)


async def test_mock_has_no_shaves_on_sunday_and_nothing_in_the_past():
    assert await mock_provider().find_slots(SHAVE, SUNDAY) == []
    today = await mock_provider(busy_percent=0).find_slots(CLASSIC, TODAY)
    assert all(s.start >= NOW + timedelta(minutes=60) for s in today)


async def test_mock_unknown_service_is_an_error():
    with pytest.raises(BookingError):
        await mock_provider().find_slots("nope", SATURDAY)


async def test_mock_booking_takes_the_slot_and_a_second_booking_fails():
    provider = mock_provider()
    slot = (await provider.find_slots(FADE, SATURDAY))[0]
    booking = await provider.book(slot, ALEX)
    assert booking.reference.startswith("KC-")
    assert booking.staff is not None and booking.slot.staff_ids == (booking.staff.id,)
    after = await provider.find_slots(FADE, SATURDAY)
    still = next((s for s in after if s.start == slot.start), None)
    assert still is None or booking.staff.id not in still.staff_ids
    if still is None:
        with pytest.raises(SlotTakenError):
            await provider.book(slot, ALEX)


async def test_mock_take_simulates_someone_else_booking_first():
    provider = mock_provider()
    slot = (await provider.find_slots(FADE, SATURDAY))[0]
    provider.take(slot)
    with pytest.raises(SlotTakenError):
        await provider.book(slot, ALEX)


def test_factory_picks_mock_by_default_and_http_when_configured():
    assert isinstance(
        build_booking_provider(make_settings(), "kingsway", KINGSWAY), MockBookingProvider
    )
    http = build_booking_provider(
        make_settings(booking_provider="http", booking_api_url="http://booking.test/"),
        "kingsway",
        KINGSWAY,
    )
    assert isinstance(http, HttpBookingProvider)
    assert str(http.client.base_url) == "http://booking.test"


# ---- HTTP adapter ----


def http_provider(handler) -> tuple[HttpBookingProvider, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.AsyncClient(
        base_url="http://booking.test", transport=httpx.MockTransport(record)
    )
    return HttpBookingProvider(client, business="kingsway", catalog=KINGSWAY), seen


def ms(hour: int, minute: int = 0) -> int:
    return int(datetime(2026, 11, 14, hour, minute, tzinfo=TZ).timestamp() * 1000)


async def test_http_find_slots_calls_the_availability_endpoint():
    body = {
        "date": "2026-11-14",
        "timezone": "America/Toronto",
        "slots": [
            {"startAt": ms(15, 30), "label": "3:30 p.m.", "staffIds": ["kingsway_stf_dani"]},
            {"startAt": ms(14), "label": "2 p.m.", "staffIds": ["a", "b"]},
        ],
    }
    provider, seen = http_provider(lambda r: httpx.Response(200, json=body))
    slots = await provider.find_slots(FADE, SATURDAY)
    assert seen[0].method == "GET"
    assert seen[0].url.path == "/api/sites/kingsway/availability"
    assert dict(seen[0].url.params) == {"service": FADE, "date": "2026-11-14"}
    assert [(s.start.hour, s.start.minute) for s in slots] == [(14, 0), (15, 30)]
    assert slots[0].start.tzinfo == TZ and slots[0].staff_ids == ("a", "b")


@pytest.mark.parametrize(
    ("respond", "error"),
    [
        (lambda r: httpx.Response(404, json={"error": "not_found"}), BookingError),
        (lambda r: httpx.Response(500, text="boom"), BookingUnavailableError),
        (lambda r: httpx.Response(200, json={"slots": [{"nope": 1}]}), BookingUnavailableError),
    ],
)
async def test_http_find_slots_errors(respond, error):
    provider, _ = http_provider(respond)
    with pytest.raises(error):
        await provider.find_slots(FADE, SATURDAY)


async def test_http_network_failure_is_unavailable():
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    provider, _ = http_provider(fail)
    with pytest.raises(BookingUnavailableError):
        await provider.find_slots(FADE, SATURDAY)


async def test_http_find_slots_rejects_unknown_service_without_calling():
    provider, seen = http_provider(lambda r: httpx.Response(200, json={"slots": []}))
    with pytest.raises(BookingError):
        await provider.find_slots("nope", SATURDAY)
    assert seen == []


def saturday_slot(*staff: str) -> Slot:
    return Slot(FADE, datetime(2026, 11, 14, 14, 0, tzinfo=TZ), staff)


async def test_http_book_posts_the_booking():
    provider, seen = http_provider(
        lambda r: httpx.Response(201, json={"bookingId": "bk_1", "manageToken": "t"})
    )
    booking = await provider.book(saturday_slot("kingsway_stf_dani"), ALEX, notes="Via chat")
    assert seen[0].method == "POST" and seen[0].url.path == "/api/sites/kingsway/bookings"
    assert json.loads(seen[0].content) == {
        "serviceId": FADE,
        "staffId": "kingsway_stf_dani",
        "startAt": ms(14),
        "name": "Alex Chen",
        "email": "alex@example.com",
        "phone": "416 555 0100",
        "notes": "Via chat",
    }
    assert booking.reference == "bk_1" and booking.staff is not None
    assert booking.staff.name == "Dani"


async def test_http_book_tries_the_next_barber_when_one_was_taken():
    replies = iter(
        [
            httpx.Response(409, json={"error": "slot_taken"}),
            httpx.Response(201, json={"bookingId": "bk_2"}),
        ]
    )
    provider, seen = http_provider(lambda r: next(replies))
    booking = await provider.book(saturday_slot("kingsway_stf_marcus", "kingsway_stf_dani"), ALEX)
    assert [json.loads(r.content)["staffId"] for r in seen] == [
        "kingsway_stf_marcus",
        "kingsway_stf_dani",
    ]
    assert booking.slot.staff_ids == ("kingsway_stf_dani",)


async def test_http_book_slot_taken_for_everyone():
    provider, _ = http_provider(lambda r: httpx.Response(409, json={"error": "slot_taken"}))
    with pytest.raises(SlotTakenError):
        await provider.book(saturday_slot("a", "b"), ALEX)


async def test_http_book_invalid_details_and_server_errors():
    provider, _ = http_provider(
        lambda r: httpx.Response(
            400,
            json={"error": "invalid", "fields": {"email": "Please enter a valid email"}},
        )
    )
    with pytest.raises(BookingError, match="valid email"):
        await provider.book(saturday_slot("a"), ALEX)
    provider, _ = http_provider(lambda r: httpx.Response(503))
    with pytest.raises(BookingUnavailableError):
        await provider.book(saturday_slot("a"), ALEX)
    provider, _ = http_provider(lambda r: httpx.Response(201))
    with pytest.raises(BookingError):
        await provider.book(saturday_slot(), ALEX)  # no staff to book with
