"""Build the Kingsway Cuts help center PDF for the booking receptionist demo.

Services, prices and lengths come from the booking catalog in `app/booking/catalog.py`, so
the help center and the receptionist always quote the same menu.

Run from backend/:  uv run python -m sample.generate_kingsway_kb
"""

from pathlib import Path

from app.booking.catalog import KINGSWAY_SERVICES
from sample.generate_kb import build_sectioned_pdf

HERE = Path(__file__).resolve().parent
PDF_OUT = HERE / "kingsway-help-center.pdf"

NAME = "Kingsway Cuts"
PHONE = "(416) 555-0187"
EMAIL = "chair@kingswaycuts.example"

Section = tuple[str, str]


def menu() -> list[Section]:
    order = ["classic", "fade", "cut-beard", "beard", "shave", "kids", "buzz"]
    by_key = {s.key: s for s in KINGSWAY_SERVICES}
    return [
        (
            f"{by_key[k].name}: {by_key[k].price}",
            f"{by_key[k].description} About {by_key[k].duration_min} minutes.",
        )
        for k in order
    ]


def pages() -> list[tuple[str, list[Section]]]:
    return [
        (
            "Visiting the shop",
            [
                (
                    "Where we are",
                    f"{NAME} is a barbershop at 2958 Bloor Street West, Toronto. We are two "
                    "minutes from Royal York station. There is street parking on Bloor and a "
                    "Green P lot behind the shop.",
                ),
                (
                    "Opening hours",
                    "Monday 9 AM to 5 PM. Tuesday 9 AM to 7 PM. Wednesday and Thursday 9 AM "
                    "to 8 PM. Friday 10 AM to 8 PM. Saturday 9 AM to 7 PM. Sunday 10 AM to "
                    "4 PM. We close on statutory holidays.",
                ),
                (
                    "Contact",
                    f"Call or text {PHONE}, or email {EMAIL}. We answer messages during "
                    "opening hours.",
                ),
                (
                    "Our barbers",
                    "Marcus owns the shop and is known for fades and tapers. Dani does "
                    "scissor work, longer styles, curls and beards, and is great with kids. "
                    "Theo does classic cuts and our hot towel shaves.",
                ),
            ],
        ),
        ("Services and prices", menu()),
        (
            "Booking, walk-ins and payment",
            [
                (
                    "How to book",
                    "Book online any time, or ask the chat on our website to find you a time. "
                    "Choose a barber or take the first one free. You get a confirmation email "
                    "with a link to change or cancel.",
                ),
                (
                    "Walk-ins",
                    "Walk-ins are welcome when a chair is free. Weekday mornings are the "
                    "quietest; Saturday afternoons are the busiest.",
                ),
                (
                    "Cancellation policy",
                    "Cancel or change your booking for free up to 2 hours before your "
                    "appointment, using "
                    "the link in your confirmation email or by calling the shop. If you are "
                    "more than 10 minutes late we may need to shorten the service or move "
                    "you to the next free time.",
                ),
                (
                    "Payment and tips",
                    "We take debit, Visa, Mastercard, Apple Pay, Google Pay and cash. Tips "
                    "can go on the card machine or in cash. Prices include the wash and "
                    "style; tax is added at checkout.",
                ),
                (
                    "Kids",
                    "The kids cut is for children 12 and under. A parent or guardian stays "
                    "in the shop during the cut. Booster seats are available.",
                ),
                (
                    "Gift cards",
                    "Gift cards are sold in the shop in any amount from $25 and never expire.",
                ),
            ],
        ),
    ]


def build_pdf(out: Path = PDF_OUT) -> Path:
    return build_sectioned_pdf(NAME, pages(), out)


if __name__ == "__main__":
    print(f"Wrote {build_pdf()}")
