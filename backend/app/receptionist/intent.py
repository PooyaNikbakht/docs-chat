"""Small, deterministic parsers for booking messages: service, day, time, contact, yes or no.

The offline receptionist runs entirely on these. The Claude path uses `is_booking_message`
to decide when to bring the booking tools in at all.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.booking.base import Service

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_WEEKDAY_RE = re.compile(
    r"\b(?:(this|next|on)\s+)?(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)"
    r"(?:day|sday|nesday|rsday|urday)?s?\b"
)
MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)
_MONTH = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

_BOOKING_WORDS = re.compile(
    r"\b(book|booking|appointment|appt|available|availability|openings?|slots?|spots?|"
    r"reserve|schedule|free times?|any times?|get in|come in|fit me in)\b"
)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\w@])\+?\d[\d\s().-]{7,}\d(?![\w@])")
_YES = re.compile(
    r"^\s*(yes|yeah|yep|yup|sure|ok|okay|confirm|confirmed|book it|go ahead|please do|"
    r"sounds good|perfect|great|do it|that works|correct)\b"
)
_NO = re.compile(r"^\s*(no|nope|nah|not that|cancel|never ?mind|change|different|another|other)\b")


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def find_service(text: str, services: Sequence[Service]) -> Service | None:
    """The first service whose keywords appear in `text` (services are ordered by specificity)."""
    t = norm(text)
    for service in services:
        for kw in (*service.keywords, service.name.lower()):
            if re.search(rf"\b{re.escape(kw)}\b", t):
                return service
    return None


def is_booking_message(text: str, services: Sequence[Service], today: date) -> bool:
    t = norm(text)
    if _BOOKING_WORDS.search(t):
        return True
    # "Can I get a fade Saturday?" names a service and a day without saying "book".
    return find_service(t, services) is not None and parse_day(t, today) is not None


def is_yes(text: str) -> bool:
    return bool(_YES.search(norm(text)))


def is_no(text: str) -> bool:
    return bool(_NO.search(norm(text)))


# ---- days ----


def parse_day(text: str, today: date) -> date | None:
    t = norm(text)
    if re.search(r"\bday after tomorrow\b", t):
        return today + timedelta(days=2)
    if re.search(r"\b(today|tonight|this (morning|afternoon|evening))\b", t):
        return today
    if re.search(r"\b(tomorrow|tmrw|tmr)\b", t):
        return today + timedelta(days=1)
    if re.search(r"\bthis weekend\b|\bweekend\b", t):
        return _next_weekday(today, 5, include_today=True)
    explicit = _explicit_date(t, today)
    if explicit:
        return explicit
    m = _WEEKDAY_RE.search(t)
    if m:
        prefix, stem = m.group(1), m.group(2)
        weekday = next(i for i, name in enumerate(WEEKDAYS) if name.startswith(stem[:3]))
        day = _next_weekday(today, weekday, include_today=prefix != "next")
        if prefix == "next" and day == today:
            day += timedelta(days=7)
        return day
    return None


def parse_iso(value: str | None) -> date | None:
    """A YYYY-MM-DD date, or None."""
    try:
        return datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return None


def _next_weekday(today: date, weekday: int, *, include_today: bool) -> date:
    ahead = (weekday - today.weekday()) % 7
    if ahead == 0 and not include_today:
        ahead = 7
    return today + timedelta(days=ahead)


def _explicit_date(t: str, today: date) -> date | None:
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        return _safe_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(rf"\b{_MONTH}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", t)
    if m:
        return _roll_year(today, _month_index(m.group(1)), int(m.group(2)))
    m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{_MONTH}", t)
    if m:
        return _roll_year(today, _month_index(m.group(2)), int(m.group(1)))
    m = re.search(r"\b(\d{1,2})/(\d{1,2})\b", t)
    if m:
        return _roll_year(today, int(m.group(1)), int(m.group(2)))
    m = re.search(r"\bthe (\d{1,2})(?:st|nd|rd|th)\b", t)
    if m:
        day = _safe_date(today.year, today.month, int(m.group(1)))
        if day and day < today:
            month = today.month % 12 + 1
            day = _safe_date(today.year + (month == 1), month, int(m.group(1)))
        return day
    return None


def _month_index(word: str) -> int:
    return next(i + 1 for i, name in enumerate(MONTHS) if name.startswith(word[:3]))


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _roll_year(today: date, month: int, day: int) -> date | None:
    d = _safe_date(today.year, month, day)
    if d and d < today:
        d = _safe_date(today.year + 1, month, day)
    return d


# ---- times ----


@dataclass(frozen=True)
class Window:
    """Part of a day, in minutes from midnight: start inclusive, end exclusive."""

    start: int
    end: int
    label: str

    def contains(self, t: datetime) -> bool:
        minutes = t.hour * 60 + t.minute
        return self.start <= minutes < self.end


def parse_window(text: str) -> Window | None:
    t = norm(text)
    m = re.search(r"\b(after|before)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", t)
    if m:
        minutes = _to_minutes(int(m.group(2)), int(m.group(3) or 0), m.group(4))
        if minutes is not None:
            label = f"{m.group(1)} {format_minutes(minutes)}"
            if m.group(1) == "after":
                return Window(minutes, 24 * 60, label)
            return Window(0, minutes, label)
    if re.search(r"\bbefore (noon|lunch)\b", t):
        return Window(0, 12 * 60, "before noon")
    if re.search(r"\bmorning\b", t):
        return Window(0, 12 * 60, "in the morning")
    if re.search(r"\b(lunch|lunchtime|midday)\b", t):
        return Window(11 * 60 + 30, 13 * 60 + 30, "around lunch")
    if re.search(r"\bafternoon\b", t):
        return Window(12 * 60, 17 * 60, "in the afternoon")
    if re.search(r"\b(evening|tonight|after work)\b", t):
        return Window(17 * 60, 24 * 60, "in the evening")
    return None


def parse_time(text: str) -> time | None:
    """A specific clock time such as "2pm", "2:30 PM", "14:00" or "at 3"."""
    t = norm(text)
    t = re.sub(r"\b(after|before)\s+\d{1,2}(:\d{2})?\s*(am|pm|a\.m\.|p\.m\.)?", " ", t)
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)", t)
    if not m:
        m = re.search(r"\b(\d{1,2}):(\d{2})()\b", t)
    if not m:
        m = re.search(r"\b(?:at|around|for)\s+(\d{1,2})()()\b(?!\s*(?:st|nd|rd|th|/))", t)
    if not m:
        return None
    minutes = _to_minutes(int(m.group(1)), int(m.group(2) or 0), m.group(3) or None)
    if minutes is None:
        return None
    return time(minutes // 60, minutes % 60)


def _to_minutes(hour: int, minute: int, meridiem: str | None) -> int | None:
    if minute > 59 or hour > 23:
        return None
    if meridiem:
        if hour < 1 or hour > 12:
            return None
        pm = meridiem.startswith("p")
        hour = hour % 12 + (12 if pm else 0)
    elif hour <= 7:
        hour += 12  # "at 3" in a barbershop means the afternoon
    return hour * 60 + minute


def format_minutes(minutes: int) -> str:
    return format_time(time(minutes // 60 % 24, minutes % 60))


def format_time(t: time | datetime) -> str:
    hour = t.hour % 12 or 12
    suffix = "AM" if t.hour < 12 else "PM"
    return f"{hour}:{t.minute:02d} {suffix}"


def day_label(day: date, today: date) -> str:
    """ "today", "tomorrow", "Saturday" within the week, else "Saturday, November 21"."""
    delta = (day - today).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "tomorrow"
    if 1 < delta < 7:
        return WEEKDAYS[day.weekday()].capitalize()
    return f"{WEEKDAYS[day.weekday()].capitalize()}, {MONTHS[day.month - 1].capitalize()} {day.day}"


def short_day(day: date) -> str:
    weekday = WEEKDAYS[day.weekday()][:3].capitalize()
    return f"{weekday}, {MONTHS[day.month - 1][:3].capitalize()} {day.day}"


def times_in(text: str) -> set[str]:
    """Clock times mentioned in a reply, normalized like `format_time` ("2:00 PM")."""
    found: set[str] = set()
    for m in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)", text.lower()):
        minutes = _to_minutes(int(m.group(1)), int(m.group(2) or 0), m.group(3))
        if minutes is not None:
            found.add(format_minutes(minutes))
    return found


# ---- contact details ----


@dataclass(frozen=True)
class ContactDetails:
    name: str | None
    email: str | None
    phone: str | None


_NAME_LEADS = re.compile(
    r"\b(?:my name is|my name's|name is|name:|i'm|i am|this is|it's|it is|under|for)\s+"
    r"([A-Za-z][A-Za-z'\-]*(?:\s+[A-Za-z][A-Za-z'\-]*){0,3})",
    re.IGNORECASE,
)
_FILLER = {
    "and",
    "my",
    "email",
    "e-mail",
    "phone",
    "number",
    "is",
    "at",
    "name",
    "please",
    "thanks",
    "thank",
    "you",
    "it's",
    "its",
    "the",
    "me",
    "or",
    "call",
    "text",
    "cell",
    "mobile",
    "reach",
    "can",
    "on",
    "with",
    "here",
    "sure",
    "ok",
    "okay",
    "yes",
}


def parse_contact(text: str) -> ContactDetails:
    email_m = EMAIL_RE.search(text)
    email = email_m.group(0).lower() if email_m else None
    rest = EMAIL_RE.sub(" ", text)
    phone_m = PHONE_RE.search(rest)
    phone = " ".join(phone_m.group(0).split()) if phone_m else None
    if phone_m:
        rest = rest.replace(phone_m.group(0), " ")
    name = None
    lead = _NAME_LEADS.search(rest)
    if lead:
        name = _clean_name(lead.group(1))
    if not name:
        name = _clean_name(rest)
    return ContactDetails(name=name, email=email, phone=phone)


def _clean_name(raw: str) -> str | None:
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)
    kept: list[str] = []
    for w in words:
        if w.lower() in _FILLER:
            if kept:
                break
            continue
        kept.append(w)
        if len(kept) == 3:
            break
    if not kept or len(" ".join(kept)) < 2:
        return None
    return " ".join(w if w[0].isupper() else w.capitalize() for w in kept)
