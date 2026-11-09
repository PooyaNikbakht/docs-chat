"""The demo barbershop's services, barbers and weekly hours.

Ids match the ones the business's booking system uses, so the HTTP adapter and the mock
agree on what a service is. The weekly hours drive the mock schedule only; the real system
keeps its own.
"""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from app.booking.base import Catalog, Service, Staff

KINGSWAY_SLUG = "kingsway"


def _svc(key: str, name: str, minutes: int, cents: int, desc: str, *kw: str) -> Service:
    return Service(
        id=f"kingsway_svc_{key}",
        key=key,
        name=name,
        duration_min=minutes,
        price_cents=cents,
        description=desc,
        keywords=kw,
    )


# Keywords are matched in this order, so the specific services come before "haircut".
KINGSWAY_SERVICES = (
    _svc(
        "cut-beard",
        "Haircut and beard",
        60,
        6200,
        "Any cut plus a beard shape with a straight-razor line-up.",
        "haircut and beard",
        "cut and beard",
        "hair and beard",
        "cut + beard",
    ),
    _svc(
        "kids",
        "Kids cut",
        25,
        2800,
        "For 12 and under.",
        "kids",
        "kid",
        "son",
        "daughter",
        "child",
        "boy",
    ),
    _svc("buzz", "Buzz cut", 20, 2600, "One guard all over, clean neckline.", "buzz"),
    _svc(
        "fade",
        "Skin fade",
        45,
        4500,
        "Bald or skin fade blended into any length on top.",
        "skin fade",
        "fade",
        "taper",
    ),
    _svc(
        "shave",
        "Hot towel shave",
        40,
        4200,
        "Hot towels and a straight-razor shave.",
        "hot towel",
        "shave",
    ),
    _svc(
        "beard",
        "Beard trim and line-up",
        20,
        2500,
        "Shape, trim and razor edges.",
        "beard",
        "line-up",
        "line up",
        "lineup",
    ),
    _svc(
        "classic",
        "Classic haircut",
        30,
        3800,
        "Scissor and clipper cut, neck shave and style.",
        "classic",
        "haircut",
        "hair cut",
        "cut",
        "trim",
    ),
)

KINGSWAY_STAFF = (
    Staff("kingsway_stf_marcus", "Marcus"),
    Staff("kingsway_stf_dani", "Dani"),
    Staff("kingsway_stf_theo", "Theo"),
)

KINGSWAY = Catalog(
    timezone=ZoneInfo("America/Toronto"),
    services=KINGSWAY_SERVICES,
    staff=KINGSWAY_STAFF,
)


@dataclass(frozen=True)
class Shift:
    """Working hours for one barber on one weekday (Monday is 0), with an optional break."""

    weekday: int
    start: str  # "09:00"
    end: str
    break_start: str | None = None
    break_end: str | None = None


@dataclass(frozen=True)
class Barber:
    staff_id: str
    services: frozenset[str]  # service keys
    shifts: tuple[Shift, ...]


ALL = frozenset(s.key for s in KINGSWAY_SERVICES)


def _days(days: list[int], start: str, end: str, brk: tuple[str, str] | None) -> list[Shift]:
    return [Shift(d, start, end, *(brk or (None, None))) for d in days]


KINGSWAY_WEEK = (
    Barber(
        "kingsway_stf_marcus",
        ALL,
        tuple(_days([1, 2, 3, 4, 5], "10:00", "19:00", ("14:00", "14:30"))),
    ),
    Barber(
        "kingsway_stf_dani",
        ALL - {"shave"},
        tuple(
            _days([2, 3, 4], "12:00", "20:00", ("16:00", "16:30"))
            + _days([5], "09:00", "17:00", None)
            + _days([6], "10:00", "16:00", None)
        ),
    ),
    Barber(
        "kingsway_stf_theo",
        ALL - {"fade"},
        tuple(
            _days([0, 1, 2, 3], "09:00", "17:00", ("12:30", "13:00"))
            + _days([5], "09:00", "15:00", ("12:30", "13:00"))
        ),
    ),
)
