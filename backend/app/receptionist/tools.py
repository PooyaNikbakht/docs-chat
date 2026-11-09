"""The booking tools Claude can call, their schemas, and a validating executor.

Every call goes through the booking desk, so a tool can only offer times the booking system
returned, can only stage a time that was offered, and can only write a booking the visitor
confirmed on a later message.
"""

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.booking.base import BookingError, BookingUnavailableError, Catalog, SlotTakenError
from app.models import BookingEvent, ChoicesEvent
from app.receptionist.desk import Availability, BookingDesk, DeskError
from app.receptionist.intent import Window, day_label, format_time, parse_iso

logger = logging.getLogger(__name__)

WINDOWS = {
    "morning": Window(0, 12 * 60, "in the morning"),
    "afternoon": Window(12 * 60, 17 * 60, "in the afternoon"),
    "evening": Window(17 * 60, 24 * 60, "in the evening"),
}


def tool_definitions(catalog: Catalog) -> list[dict[str, Any]]:
    keys = [s.key for s in catalog.services]
    empty = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    return [
        {
            "name": "list_services",
            "description": "List the services we offer, with price and length in minutes.",
            "strict": True,
            "input_schema": empty,
        },
        {
            "name": "check_availability",
            "description": (
                "Look up open start times for one service on one day in the booking system. "
                "This is the only source of open times. Returns up to six times with a "
                "slot_id each, how many are open in total, and the next day with openings "
                "if the day is full. The widget shows the returned times as buttons."
            ),
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "enum": keys, "description": "Service key"},
                    "date": {"type": "string", "description": "Day to check, YYYY-MM-DD"},
                    "time_of_day": {
                        "type": "string",
                        "enum": ["any", "morning", "afternoon", "evening"],
                    },
                },
                "required": ["service", "date", "time_of_day"],
                "additionalProperties": False,
            },
        },
        {
            "name": "request_booking",
            "description": (
                "Stage a booking for a time the visitor picked from check_availability "
                "results. Nothing is booked yet: the widget shows a summary with a Book it "
                "button, and you must ask the visitor to confirm. Needs their name and email; "
                "phone may be an empty string."
            ),
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "slot_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                },
                "required": ["slot_id", "name", "email", "phone"],
                "additionalProperties": False,
            },
        },
        {
            "name": "confirm_booking",
            "description": (
                "Write the staged booking to the booking system. Call it only after the "
                "visitor clearly said yes to the summary in a later message."
            ),
            "strict": True,
            "input_schema": empty,
        },
    ]


class _NoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _CheckInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service: str = Field(min_length=1, max_length=40)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time_of_day: Literal["any", "morning", "afternoon", "evening"] = "any"


class _StageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slot_id: str = Field(min_length=1, max_length=64)
    name: str = Field(max_length=120)
    email: str = Field(max_length=200)
    phone: str = Field(default="", max_length=40)


class ToolRun:
    """Runs tool calls for one visitor message and keeps the widget events they produce."""

    def __init__(self, desk: BookingDesk) -> None:
        self.desk = desk
        self.choices: ChoicesEvent | None = None
        self.booking: BookingEvent | None = None
        self.time_labels: set[str] = set()  # every time a tool returned this message

    async def run(self, name: str, raw: Any) -> tuple[dict[str, Any], bool]:
        """Returns (result, is_error). Invalid input never reaches the booking system."""
        try:
            if name == "list_services":
                _NoInput.model_validate(raw or {})
                return self._services(), False
            if name == "check_availability":
                return await self._check(_CheckInput.model_validate(raw)), False
            if name == "request_booking":
                return self._stage(_StageInput.model_validate(raw)), False
            if name == "confirm_booking":
                _NoInput.model_validate(raw or {})
                return await self._confirm(), False
            return {"error": "unknown_tool", "message": f"No tool named {name}."}, True
        except ValidationError as exc:
            detail = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
            return {"error": "invalid_input", "message": detail[:300]}, True
        except DeskError as exc:
            return {"error": exc.code, "message": exc.message}, True
        except BookingUnavailableError:
            raise
        except BookingError as exc:
            return {"error": exc.code, "message": exc.message}, True

    def _services(self) -> dict[str, Any]:
        return {
            "services": [
                {
                    "service": s.key,
                    "name": s.name,
                    "price": s.price,
                    "minutes": s.duration_min,
                    "description": s.description,
                }
                for s in self.desk.catalog.services
            ]
        }

    async def _check(self, args: _CheckInput) -> dict[str, Any]:
        service = self.desk.service_by_key_or_id(args.service)
        if service is None:
            raise DeskError("unknown_service", "Use a service key from list_services.")
        day = parse_iso(args.date)
        if day is None:
            raise DeskError("invalid_date", "Use a real date in YYYY-MM-DD form.")
        window = WINDOWS.get(args.time_of_day)
        avail = await self.desk.availability(service, day, window)
        return self._availability_result(avail)

    def _availability_result(self, avail: Availability) -> dict[str, Any]:
        today = self.desk.today
        result: dict[str, Any] = {
            "service": avail.service.name,
            "date": avail.day.isoformat(),
            "day": day_label(avail.day, today),
            "open_count": len(avail.slots),
            "times": [self._time(sid, s) for sid, s in avail.shown],
        }
        if avail.window_empty and avail.window:
            result["note"] = f"Nothing open {avail.window.label}; these are the other open times."
        if avail.shown:
            self.choices = self.desk.slot_choices(avail.day, avail.shown)
        if not avail.slots:
            result["note"] = "Fully booked that day."
            if avail.next_day:
                result["next_available"] = {
                    "date": avail.next_day.isoformat(),
                    "day": day_label(avail.next_day, today),
                    "times": [self._time(sid, s) for sid, s in avail.next_shown],
                }
                self.choices = self.desk.slot_choices(avail.next_day, avail.next_shown)
        return result

    def _time(self, slot_id: str, slot: Any) -> dict[str, str]:
        label = format_time(slot.start)
        self.time_labels.add(label)
        return {"slot_id": slot_id, "time": label}

    def _stage(self, args: _StageInput) -> dict[str, Any]:
        event = self.desk.stage(args.slot_id, args.name, args.email, args.phone)
        self.booking = event
        self.time_labels.add(event.when.rsplit(", ", 1)[-1])
        return {
            "status": "awaiting_confirmation",
            "summary": f"{event.service}, {event.when}, for {event.name} ({event.contact})",
            "next_step": "Ask the visitor to confirm. The widget shows a Book it button.",
        }

    async def _confirm(self) -> dict[str, Any]:
        pending = self.desk.state.pending
        try:
            booking, event = await self.desk.confirm()
        except SlotTakenError:
            assert pending is not None
            service = self.desk.service(pending.slot.service_id)
            taken = format_time(pending.slot.start)
            self.time_labels.add(taken)
            result: dict[str, Any] = {"status": "slot_taken", "time": taken}
            if service:
                avail = await self.desk.availability(service, pending.slot.start.date(), None)
                result["alternatives"] = self._availability_result(avail)
            return result
        self.booking = event
        self.time_labels.add(format_time(booking.slot.start))
        return {
            "status": "booked",
            "reference": booking.reference,
            "summary": f"{event.service}, {event.when}"
            + (f", with {event.staff}" if event.staff else ""),
        }


def tool_result_block(tool_use_id: str, result: dict[str, Any], is_error: bool) -> dict[str, Any]:
    block: dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": json.dumps(result),
    }
    if is_error:
        block["is_error"] = True
    return block
