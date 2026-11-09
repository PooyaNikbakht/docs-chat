"""Build the Harbourview Bakery help center PDF for the bakery's support bot.

Every fact comes from the bakery's WordPress site (site-rescue/seed/build-content.php):
the menu and prices, hours, location, cake orders and the holiday order guide. Keep the two
in step, so the bot never says something the website doesn't.

Run from backend/:  uv run python -m sample.generate_harbourview_kb
"""

from pathlib import Path

from sample.generate_kb import build_sectioned_pdf

HERE = Path(__file__).resolve().parent
PDF_OUT = HERE / "harbourview-help-center.pdf"

NAME = "Harbourview Bakery"
PHONE = "416-555-0142"
EMAIL = "hello@harbourview-bakery.example"

Section = tuple[str, str]


def pages() -> list[tuple[str, list[Section]]]:
    return [
        (
            "Visiting the bakery",
            [
                (
                    "Where are you located? Address and parking",
                    "We are located at 48 Harbour Lane, Toronto, a short walk from the water. "
                    "There is street parking on Harbour Lane, and the streetcar stop is a "
                    "two minute walk.",
                ),
                (
                    "Opening hours: when are you open?",
                    "We are open Tuesday to Sunday and closed on Mondays. Tuesday to Friday "
                    "we are open 7:00 am to 6:00 pm, Saturday 7:00 am to 4:00 pm, and Sunday "
                    "8:00 am to 2:00 pm.",
                ),
                (
                    "Contact",
                    f"Call {PHONE} or email {EMAIL}.",
                ),
                (
                    "About us",
                    "We started in 2014 as a two person stall at a weekend market and are now "
                    "a team of eleven bakers, pastry cooks and counter staff. Every dough is "
                    "mixed by hand, and we still use the starter from that first market "
                    "season. We still close when the bread runs out.",
                ),
                (
                    "Ingredients and sourcing",
                    "Our flour comes from an Ontario mill, our butter from a family dairy, "
                    "and our fruit from farms within a few hours of the city. Day old bread "
                    "goes to a local food bank every evening.",
                ),
            ],
        ),
        (
            "Menu and prices",
            [
                (
                    "Bread",
                    "Country sourdough $9.50 (our 36 hour loaf, with a crackly crust and an "
                    "open crumb). Seeded rye $10.00. Olive and rosemary $11.00. Whole wheat "
                    "sandwich loaf $8.00. Focaccia slab $7.50.",
                ),
                (
                    "Croissants and pastries",
                    "A butter croissant is $4.25; our other croissants are pain au chocolat "
                    "$4.75, almond croissant $5.50 and ham and gruyere croissant $6.75. "
                    "Seasonal fruit danish $5.25.",
                ),
                (
                    "Sweets",
                    "Cardamom cinnamon bun $4.50. Brown butter chocolate chip cookie $3.25. "
                    "Lemon tart $6.00. Maple pecan blondie $4.00.",
                ),
                (
                    "Celebration cakes",
                    "6 inch round, serves 8 to 10: from $55. 8 inch round, serves 12 to 16: "
                    "from $80. Two tier, serves 30 to 40: from $240. Flavours: vanilla bean, "
                    "dark chocolate, lemon raspberry, and carrot with brown butter cream "
                    "cheese.",
                ),
            ],
        ),
        (
            "Custom and wedding cakes",
            [
                (
                    "How to order a custom cake",
                    "Every custom cake is designed with you. Fill in the form on our Custom "
                    "Cakes page with your date, the number of guests and any ideas you have. "
                    "Our cake team replies within two business days with sketches and a "
                    "quote.",
                ),
                (
                    "How much notice we need",
                    "At least 5 days for celebration cakes and 4 weeks for wedding cakes.",
                ),
                (
                    "Cake tastings",
                    "You can do a cake tasting with us on Tuesdays.",
                ),
                (
                    "Wedding cakes: deposit, delivery and setup",
                    "A 30 percent deposit holds your date. We deliver anywhere in the city "
                    "and set up the cake on site: our team arrives two hours before the "
                    "reception to assemble and finish it, and leaves serving instructions "
                    "with your venue coordinator.",
                ),
            ],
        ),
        (
            "Holiday orders",
            [
                (
                    "When holiday pre-orders open",
                    "Holiday pre-orders open on November 15.",
                ),
                (
                    "What is on the holiday menu",
                    "Stollen with marzipan, panettone (orange and dark chocolate), "
                    "gingerbread cookie tins, Bûche de Noël (serves 8), and country "
                    "sourdough and seeded rye reserved for pick-up.",
                ),
                (
                    "Holiday pick-up days",
                    "You can pick up holiday orders December 21 to 24, from 8 am to 3 pm. "
                    "We are closed December 25 and 26.",
                ),
                (
                    "How to place a holiday order",
                    "Call the shop, or use the order form on our Custom Cakes page and "
                    'mention "holiday order" in the message. Payment is taken at pick-up.',
                ),
            ],
        ),
    ]


def build_pdf(out: Path = PDF_OUT) -> Path:
    return build_sectioned_pdf(NAME, pages(), out)


if __name__ == "__main__":
    print(f"Wrote {build_pdf()}")
