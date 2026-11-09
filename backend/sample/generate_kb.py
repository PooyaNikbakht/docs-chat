"""Build the Northwind demo content from one fact sheet.

Reads `northwind-facts.md` and writes:
- `northwind-help-center.pdf`: the customer help center the support bot answers from
- `frontend/src/data/northwind.json`: the facts the sample website renders

Both come from the same facts, so the website and the bot always agree.

Run from backend/:  uv run python sample/generate_kb.py
"""

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

HERE = Path(__file__).resolve().parent
FACTS = HERE / "northwind-facts.md"
PDF_OUT = HERE / "northwind-help-center.pdf"
JSON_OUT = HERE.parents[1] / "frontend" / "src" / "data" / "northwind.json"

Facts = dict[str, Any]


# ---- Parsing the fact sheet ----


def _slug(heading: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", heading).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_facts(text: str) -> Facts:
    """`key: value` bullets become a dict and a table becomes a list of rows, per heading.

    A section with both gets the table under `rows`.
    """
    facts: Facts = {}
    section: str | None = None
    table: list[list[str]] = []

    def flush_table() -> None:
        if section and len(table) >= 2:
            header, rows = table[0], table[2:]  # table[1] is the --- separator
            parsed = [dict(zip(header, r, strict=True)) for r in rows]
            target = facts.setdefault(section, {})
            target["rows"] = parsed
        table.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            flush_table()
            section = _slug(line[3:])
            continue
        if section is None:
            continue
        if line.startswith("|"):
            table.append(_cells(line))
            continue
        flush_table()
        match = re.match(r"^- ([a-z_]+): (.+)$", line)
        if match and section:
            facts.setdefault(section, {})[match.group(1)] = match.group(2).strip()
    flush_table()
    return facts


def load_facts(path: Path = FACTS) -> Facts:
    return parse_facts(path.read_text(encoding="utf-8"))


def money(value: str | int) -> str:
    return f"${int(value)}"


def site_data(f: Facts) -> Facts:
    """The subset of facts the sample website renders, with numbers as numbers."""
    shipping = f["shipping"]
    return {
        "business": f["business"],
        "shipping": {
            **{k: v for k, v in shipping.items() if k != "rows"},
            "free_canada_over": int(shipping["free_canada_over"]),
            "free_us_over": int(shipping["free_us_over"]),
            "rates": [{**r, "price": int(r["price"])} for r in shipping["rows"]],
        },
        "returns": f["returns"],
        "subscriptions": {
            **f["subscriptions"],
            "discount_percent": int(f["subscriptions"]["discount_percent"]),
        },
        "coffees": [
            {
                **{k: v for k, v in c.items() if k not in ("price", "notes", "use")},
                "price": int(c["price"]),
                "notes": [n.strip() for n in c["notes"].split(",")],
                "use": [u.strip() for u in c["use"].split(",")],
            }
            for c in f["coffees"]["rows"]
        ],
        "coffee_notes": f["coffee_notes"],
        "brewing": f["brewing"]["rows"],
        "gift_cards": {
            **f["gift_cards"],
            "amounts": [int(a) for a in re.findall(r"\d+", f["gift_cards"]["amounts"])],
        },
        "wholesale": f["wholesale"],
        "cafes": f["cafes"]["rows"],
        "cafe_notes": f["cafes_notes"],
    }


# ---- Help center text ----

Section = tuple[str, str]  # (heading, paragraph)
Page = tuple[str, list[Section]]


def help_center_pages(f: Facts) -> list[Page]:
    b, ship, ret, sub = f["business"], f["shipping"], f["returns"], f["subscriptions"]
    notes, gift, whole = f["coffee_notes"], f["gift_cards"], f["wholesale"]
    rates = {(r["zone"], r["method"]): r for r in ship["rows"]}
    ca_std, ca_exp = rates[("Canada", "Standard")], rates[("Canada", "Express")]
    us_std = rates[("United States", "Standard")]
    pickup = rates[("Local pickup", "Harbour Street café")]
    coffees = f["coffees"]["rows"]
    brewing = {r["method"]: r for r in f["brewing"]["rows"]}
    cafes = f["cafes"]["rows"]
    cafe_notes = f["cafes_notes"]
    name = b["name"]

    def listing(items: str) -> str:
        parts = [p.strip() for p in items.split(",")]
        return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"

    def coffee_line(c: dict[str, str]) -> str:
        return (
            f"{c['name']} is a {c['roast'].lower()} roast from {c['origin']} "
            f"({c['region']}), {c['process'].lower()}. {c['name']} tastes of "
            f"{listing(c['notes'])}. {c['name']} is best for {listing(c['use'])}. "
            f"A {b['bag_size']} bag of {c['name']} costs {money(c['price'])}."
        )

    def brew_line(method: str, extra: str) -> str:
        r = brewing[method]
        lead = method if method[0].isupper() and " " in method else method.lower()
        return (
            f"For {lead}, use {r['dose']} of coffee for {r['yield']}, a {r['ratio']} ratio. "
            f"Grind {r['grind']}, use water at {r['temperature']}, and brew for "
            f"{r['time']}. {extra}"
        )

    def cafe_line(c: dict[str, str]) -> str:
        sunday = "closed on Sunday" if c["sunday"] == "closed" else f"{c['sunday']} on Sunday"
        return (
            f"Our {c['name']} café is at {c['address']}. Opening hours at {c['name']} are "
            f"{c['weekdays']} Monday to Friday, {c['saturday']} on Saturday, and {sunday}. "
            f"{c['note']}"
        )

    return [
        (
            "Welcome to our help center",
            [
                (
                    "About this guide",
                    f"This guide answers the questions customers ask us most about ordering, "
                    f"shipping, returns, subscriptions, our coffees, brewing, gift cards, "
                    f"wholesale and our cafés. {name} is a fictional business made up for a "
                    f"software demo, and every name, address and price in this guide is "
                    f"invented.",
                ),
                (
                    "Who we are",
                    f"{name} is a small-batch roaster in {b['city']}, founded in "
                    f"{b['founded']} by {b['founders']}. We roast on {b['roaster']}, and we run "
                    f"three cafés.",
                ),
                (
                    "Getting help from a person",
                    f"Our support team is available {b['support_hours']}. Email "
                    f"{b['email']} or call {b['phone']}, and we reply {b['reply_time']}. "
                    f"Please include your order number if your question is about an order.",
                ),
            ],
        ),
        (
            "Ordering and shipping",
            [
                (
                    "Where we ship",
                    f"We ship to {ship['countries']}, including every US state. "
                    f"{ship['no_ship_note']} All prices are "
                    f"in Canadian dollars ({b['currency']}).",
                ),
                (
                    "When your order ships",
                    f"We roast {ship['roast_days']}. Orders placed before "
                    f"{ship['order_cutoff']} on a roast day are roasted and shipped the next "
                    f"business day. {ship['tracking']}",
                ),
                (
                    "Shipping times and costs",
                    f"Standard shipping in Canada costs {money(ca_std['price'])} and takes "
                    f"{ca_std['time']}. Express shipping in Canada costs "
                    f"{money(ca_exp['price'])} and takes {ca_exp['time']}. Standard shipping "
                    f"to the United States (US) costs {money(us_std['price'])} and takes "
                    f"{us_std['time']}.",
                ),
                (
                    "Free shipping",
                    f"Shipping is free on orders over {money(ship['free_canada_over'])} in "
                    f"Canada and over {money(ship['free_us_over'])} to the United States. "
                    f"Local pickup from our {pickup['method']} is always free, and orders are "
                    f"ready the next business day.",
                ),
                (
                    "Changing an order",
                    f"You can change the address or items on an order within "
                    f"{ship['address_change_window']} of placing it. Email {b['email']} with "
                    f"your order number. After that, the order may already be roasting.",
                ),
            ],
        ),
        (
            "Returns and refunds",
            [
                ("Our taste guarantee", ret["guarantee"]),
                (
                    "Returning brewing gear",
                    f"{ret['gear']} {ret['return_shipping']}",
                ),
                ("Damaged or wrong items", ret["damaged"]),
                (
                    "How refunds work",
                    f"{ret['refund_time']} {ret['final_sale']} To start a return, email "
                    f"{b['email']} with your order number.",
                ),
            ],
        ),
        (
            "Subscriptions",
            [
                (
                    "How subscriptions work",
                    f"A subscription delivers fresh coffee {sub['frequencies']}, and you choose "
                    f"the coffee, the grind and the frequency. Subscribers save "
                    f"{sub['discount_percent']} percent on every bag. {sub['free_shipping']}",
                ),
                (
                    "Pause or skip a delivery",
                    f"You can pause your subscription for up to {sub['pause_max']} at a time, "
                    f"and it restarts automatically on the date you pick. {sub['skip']} "
                    f"Changes must be made at least {sub['change_deadline']}.",
                ),
                (
                    "Change or cancel",
                    f"You can change your coffee, grind, frequency or address at any time. "
                    f"{sub['cancel']} Changes and cancellations made at least "
                    f"{sub['change_deadline']} apply to that delivery.",
                ),
                ("Roaster's Choice", sub["roasters_choice"]),
                ("Managing your subscription", sub["manage"]),
            ],
        ),
        (
            "Our coffees",
            [
                ("Roast levels", notes["roast_levels"]),
                *[(c["name"], coffee_line(c)) for c in coffees],
                ("How decaf is made", notes["decaf_process"]),
                ("Freshness and grind options", f"{notes['freshness']} {notes['grind']}"),
                ("Allergens", notes["allergens"]),
                ("Sourcing", notes["sourcing"]),
            ],
        ),
        (
            "Brewing guides",
            [
                (
                    "Pour-over",
                    brew_line(
                        "Pour-over",
                        "Bloom with twice the coffee's weight in water for 30 seconds first.",
                    ),
                ),
                (
                    "French press",
                    brew_line(
                        "French press",
                        "Stir after one minute, press slowly at four minutes, and pour right away.",
                    ),
                ),
                (
                    "Espresso",
                    brew_line(
                        "Espresso",
                        "If a shot runs fast and tastes sour, grind finer. If it runs slow and "
                        "tastes bitter, grind coarser.",
                    ),
                ),
                (
                    "Storing coffee",
                    "Keep beans in their resealable bag or an airtight container, away from "
                    "light and heat. Don't keep coffee in the fridge. Grind just before "
                    "brewing for the best flavour.",
                ),
            ],
        ),
        (
            "Gift cards and wholesale",
            [
                (
                    "Gift cards",
                    f"Gift cards come in {re.sub(r'(\d+)', r'$\1', gift['amounts'])} amounts. "
                    f"{gift['delivery']} {gift['expiry']} {gift['use']} {gift['refunds']}",
                ),
                (
                    "Wholesale for businesses",
                    f"We supply {whole['who']}. The minimum order is {whole['minimum']}. "
                    f"{whole['delivery']} {whole['training']}",
                ),
                ("Becoming a wholesale partner", whole["contact"]),
            ],
        ),
        (
            "Cafés, hours and contact",
            [
                *[(f"{c['name']} café", cafe_line(c)) for c in cafes],
                (
                    "Holidays and amenities",
                    f"{cafe_notes['holidays']} {cafe_notes['wifi']} {cafe_notes['pets']}",
                ),
                (
                    "Contact us",
                    f"Email {b['email']} or call {b['phone']}, {b['support_hours']}. For "
                    f"wholesale, email {b['wholesale_email']}.",
                ),
            ],
        ),
    ]


# ---- PDF ----


class HelpCenter(FPDF):
    title_text = "Help Center"

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "", 9)
        self.set_text_color(110, 100, 90)
        self.cell(0, 8, self.title_text, new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(110, 100, 90)
        self.cell(0, 8, f"Fictional sample for demos. Page {self.page_no()}", align="C")


def build_sectioned_pdf(
    name: str, pages: list[tuple[str, list[tuple[str, str]]]], out: Path
) -> Path:
    """A help center PDF from numbered pages of (heading, body) sections."""
    pdf = HelpCenter(format="A4")
    pdf.title_text = f"{name} Help Center"
    pdf.set_creation_date(datetime(2026, 1, 1, tzinfo=UTC))
    pdf.set_title(f"{name} Help Center")
    pdf.set_author(name)
    pdf.set_margins(22, 20, 22)
    pdf.set_auto_page_break(auto=True, margin=20)
    for number, (title, sections) in enumerate(pages, start=1):
        pdf.add_page()
        if number == 1:
            pdf.set_font("Helvetica", "B", 24)
            pdf.set_text_color(17, 17, 17)
            pdf.multi_cell(0, 12, f"{name}\nHelp Center", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(110, 100, 90)
            pdf.cell(0, 8, "A fictional sample document.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(8)
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_text_color(17, 17, 17)
        pdf.cell(0, 10, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        for heading, body in sections:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(17, 24, 39)
            pdf.cell(0, 8, heading, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 6, body, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)
    pdf.output(str(out))
    return out


def build_pdf(f: Facts, out: Path = PDF_OUT) -> Path:
    name = f["business"]["name"]
    pdf = HelpCenter(format="A4")
    pdf.title_text = f"{name} Help Center"
    pdf.set_creation_date(datetime(2026, 1, 1, tzinfo=UTC))
    pdf.set_title(f"{name} Help Center")
    pdf.set_author(name)
    pdf.set_margins(22, 20, 22)
    pdf.set_auto_page_break(auto=True, margin=20)

    for number, (title, sections) in enumerate(help_center_pages(f), start=1):
        pdf.add_page()
        if number == 1:
            pdf.set_font("Helvetica", "B", 24)
            pdf.set_text_color(59, 42, 32)
            pdf.multi_cell(0, 12, f"{name}\nCustomer Help Center", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(94, 122, 90)
            pdf.cell(
                0, 8, "Edition 2026. A fictional sample document.", new_x="LMARGIN", new_y="NEXT"
            )
            pdf.ln(8)
        pdf.set_font("Helvetica", "B", 17)
        pdf.set_text_color(59, 42, 32)
        pdf.cell(0, 10, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        for heading, body in sections:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(17, 24, 39)
            pdf.cell(0, 8, heading, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 6, body, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    pdf.output(str(out))
    return out


def write_site_json(f: Facts, out: Path = JSON_OUT) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(site_data(f), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    facts = load_facts()
    print(f"Wrote {build_pdf(facts)}")
    print(f"Wrote {write_site_json(facts)}")
