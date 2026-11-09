"""Booking providers behind one interface, plus the factory that picks one from settings."""

import httpx

from app.booking.base import BookingProvider, Catalog
from app.booking.http import HttpBookingProvider
from app.booking.mock import MockBookingProvider
from app.settings import Settings


def build_booking_provider(settings: Settings, business: str, catalog: Catalog) -> BookingProvider:
    """The HTTP adapter when BOOKING_PROVIDER=http and a base URL is set, else the mock."""
    if settings.booking_provider == "http" and settings.booking_api_url:
        client = httpx.AsyncClient(
            base_url=settings.booking_api_url.rstrip("/"),
            timeout=settings.booking_timeout_seconds,
            headers={"Accept": "application/json"},
        )
        return HttpBookingProvider(client, business=business, catalog=catalog)
    return MockBookingProvider(catalog)


__all__ = ["BookingProvider", "build_booking_provider"]
