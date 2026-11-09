"""HTTP adapter for the business's booking system.

It expects two JSON endpoints under `{base_url}/api/sites/{business}`:

- `GET  /availability?service={service_id}&date=YYYY-MM-DD`
  -> `200 {"date", "timezone", "slots": [{"startAt": <epoch ms>, "label", "staffIds": [...]}]}`
- `POST /bookings` with `{"serviceId", "staffId", "startAt", "name", "email", "phone", "notes"}`
  -> `201 {"bookingId", "manageToken"}`, `409` when the time is gone, `400` with
  `{"message", "fields"}` when a detail is invalid.

The service list comes from the catalog in config, since visitors pick from a short, stable
menu and the endpoints above take its ids.
"""

import logging
from datetime import date, datetime
from typing import Any

import httpx

from app.booking.base import (
    Booking,
    BookingError,
    BookingUnavailableError,
    Catalog,
    Customer,
    Slot,
    SlotTakenError,
)

logger = logging.getLogger(__name__)

UNREACHABLE = "The booking system isn't answering right now."


class HttpBookingProvider:
    def __init__(self, client: httpx.AsyncClient, *, business: str, catalog: Catalog) -> None:
        self.client = client
        self.business = business
        self.catalog = catalog

    def _url(self, path: str) -> str:
        return f"/api/sites/{self.business}/{path}"

    async def find_slots(self, service_id: str, day: date) -> list[Slot]:
        if self.catalog.service(service_id) is None:
            raise BookingError("That service doesn't exist.")
        params = {"service": service_id, "date": day.isoformat()}
        try:
            res = await self.client.get(self._url("availability"), params=params)
        except httpx.HTTPError as exc:
            raise BookingUnavailableError(UNREACHABLE) from exc
        if res.status_code == 404:
            raise BookingError("The booking system doesn't know that service.")
        if res.status_code != 200:
            logger.warning("Availability returned %s", res.status_code)
            raise BookingUnavailableError(UNREACHABLE)
        try:
            raw = res.json().get("slots", [])
            slots = [self._slot(service_id, s) for s in raw]
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise BookingUnavailableError(UNREACHABLE) from exc
        return sorted(slots, key=lambda s: s.start)

    def _slot(self, service_id: str, raw: dict[str, Any]) -> Slot:
        start = datetime.fromtimestamp(int(raw["startAt"]) / 1000, self.catalog.timezone)
        staff = tuple(str(x) for x in raw.get("staffIds") or ())
        return Slot(service_id=service_id, start=start, staff_ids=staff)

    async def book(self, slot: Slot, customer: Customer, notes: str = "") -> Booking:
        service = self.catalog.service(slot.service_id)
        if service is None:
            raise BookingError("That service doesn't exist.")
        if not slot.staff_ids:
            raise BookingError("That time has no one free to take it.")
        last: SlotTakenError | None = None
        # The system books a specific person, so try each barber who was free at that time.
        for staff_id in slot.staff_ids:
            payload = {
                "serviceId": service.id,
                "staffId": staff_id,
                "startAt": slot.start_ms,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "notes": notes,
            }
            try:
                res = await self.client.post(self._url("bookings"), json=payload)
            except httpx.HTTPError as exc:
                raise BookingUnavailableError(UNREACHABLE) from exc
            if res.status_code == 201:
                body = _json(res)
                return Booking(
                    reference=str(body.get("bookingId", "")),
                    service=service,
                    slot=Slot(service.id, slot.start, (staff_id,)),
                    staff=self.catalog.staff_member(staff_id),
                    customer=customer,
                )
            if res.status_code == 409:
                last = SlotTakenError("That time was just booked by someone else.")
                continue
            if res.status_code == 400:
                body = _json(res)
                fields = body.get("fields") or {}
                detail = next(iter(fields.values()), None) if isinstance(fields, dict) else None
                raise BookingError(str(detail or body.get("message") or "Check your details."))
            logger.warning("Booking returned %s", res.status_code)
            raise BookingUnavailableError(UNREACHABLE)
        raise last or SlotTakenError("That time was just booked by someone else.")


def _json(res: httpx.Response) -> dict[str, Any]:
    try:
        body = res.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}
