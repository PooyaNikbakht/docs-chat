"""Support bots: who they speak for, what they answer from, and where they may be embedded.

A bot's knowledge base is ingested once at startup and pinned in memory, so it never
expires like the temporary documents on the "try your own PDF" page.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.booking.base import Catalog
from app.booking.catalog import KINGSWAY, KINGSWAY_SLUG
from app.ingest.service import ingest_pdf
from app.models import Document
from app.providers.base import Persona, make_persona
from app.settings import Settings

logger = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample"


@dataclass(frozen=True)
class BookingSetup:
    """Lets a bot check open times and book them in the business's booking system."""

    business: str  # the business's id in the booking system
    catalog: Catalog
    phone: str  # offered when the booking system can't be reached
    about: str = ""  # one line about the business for the receptionist prompt


@dataclass(frozen=True)
class Bot:
    id: str
    name: str
    business: str
    subline: str
    greeting: str
    suggestions: tuple[str, ...]
    accent_color: str
    handoff_text: str
    # A path like "/contact" is joined to PUBLIC_SITE_URL; a full URL or mailto: is used as is.
    handoff_url: str
    not_found: str
    knowledge_base: Path
    allowed_origins: tuple[str, ...] = ("*",)
    tooltip: str | None = None
    source_label: str = "Help center"
    booking: BookingSetup | None = None
    # A short help center needs smaller chunks, or BM25 has too few to tell apart.
    chunk_words: int | None = None
    # Customers on a business's site want the answer, not a page reference.
    show_sources: bool = False
    # The reply to "what can you help with?". Answered without a model, so it works in demo mode.
    about: str | None = None
    # (help center page, link label, site URL): answers citing that page offer the link instead
    # of a page reference. A path like "/shop" is joined to PUBLIC_SITE_URL.
    page_links: tuple[tuple[int, str, str], ...] = ()

    @property
    def persona(self) -> Persona:
        return make_persona(
            f"You are {self.name}, the customer support assistant on {self.business}'s "
            f'website. You speak for the business, so say "we" and "our". The user\'s message '
            f"contains numbered passages from {self.business}'s customer help center.",
            self.not_found,
            self.about,
        )

    def resolve_handoff(self, site_url: str) -> str:
        return resolve_url(self.handoff_url, site_url)


def resolve_url(url: str, site_url: str) -> str:
    """A path like "/contact" is joined to the site URL; a full URL or mailto: is used as is."""
    return site_url.rstrip("/") + url if url.startswith("/") else url


NORTHWIND = Bot(
    id="northwind",
    name="Northwind Help",
    business="Northwind Coffee Co.",
    subline="Answers from Northwind's help center",
    greeting=(
        "Hi! I can help with orders, shipping, returns, subscriptions and our coffees. "
        "What would you like to know?"
    ),
    suggestions=(
        "Can I pause my subscription?",
        "How long does shipping take to the US?",
        "Which coffee is best for espresso?",
    ),
    accent_color="#3B2A20",
    handoff_text="Talk to a human",
    handoff_url="/contact",
    not_found=(
        "I couldn't find that in our help center, so I don't want to guess. "
        "Our team can help you directly."
    ),
    knowledge_base=SAMPLE_DIR / "northwind-help-center.pdf",
    tooltip="Questions about shipping or subscriptions? Ask me.",
    about=(
        "I'm Northwind's assistant. I can answer questions about orders, shipping and returns, "
        "coffee subscriptions, and our coffees and brewing. For anything else, our team is "
        "happy to help."
    ),
    page_links=(
        (2, "Shop our coffees", "/shop"),
        (3, "Contact us", "/contact"),
        (4, "See subscriptions", "/subscriptions"),
        (5, "Shop our coffees", "/shop"),
        (6, "Shop our coffees", "/shop"),
        (7, "Read our brew guides", "/brew-guides"),
        (8, "Contact us", "/contact"),
        (9, "Visit or contact us", "/contact"),
    ),
)

KINGSWAY_BOT = Bot(
    id="kingsway",
    name="Kingsway Front Desk",
    business="Kingsway Cuts",
    subline="Books appointments and answers from our help center",
    greeting=(
        "Hi! I can check open times and book you in, or answer questions about the shop. "
        "What can I do for you?"
    ),
    suggestions=(
        "Is Saturday afternoon open for a skin fade?",
        "Book a haircut tomorrow morning",
        "What's your cancellation policy?",
    ),
    accent_color="#1F2937",
    handoff_text="Call the shop",
    handoff_url="tel:+14165550187",
    not_found=(
        "I couldn't find that in our help center, so I don't want to guess. "
        "Give the shop a call and we'll sort it out."
    ),
    knowledge_base=SAMPLE_DIR / "kingsway-help-center.pdf",
    tooltip="Need a haircut? I can book you in.",
    about=(
        "I'm the Kingsway Cuts front desk. I can check open times and book you in with any of "
        "our barbers, and answer questions about our services, prices, hours, walk-ins and "
        "cancellation policy."
    ),
    page_links=(
        (1, "Find the shop", "https://kingsway.pooya.website/#visit"),
        (2, "See services and prices", "https://kingsway.pooya.website/#menu"),
        (3, "Book online", "https://kingsway.pooya.website/book"),
    ),
    booking=BookingSetup(
        business=KINGSWAY_SLUG,
        catalog=KINGSWAY,
        phone="(416) 555-0187",
        about="Kingsway Cuts is a barbershop in Toronto with three barbers.",
    ),
)

HARBOURVIEW = Bot(
    id="harbourview",
    name="Harbourview Help",
    business="Harbourview Bakery",
    subline="Answers from the bakery's help center",
    greeting=(
        "Hi! I can help with our hours, menu, custom and wedding cakes, and holiday orders. "
        "What would you like to know?"
    ),
    suggestions=(
        "Are you open on Mondays?",
        "How much notice do you need for a cake?",
        "How much is a sourdough loaf?",
    ),
    accent_color="#6B4423",
    handoff_text="Call the bakery",
    handoff_url="tel:+14165550142",
    not_found=(
        "I couldn't find that in our help center, so I don't want to guess. "
        "Give the bakery a call and we'll help."
    ),
    knowledge_base=SAMPLE_DIR / "harbourview-help-center.pdf",
    tooltip="Questions about cakes or hours? Ask me.",
    chunk_words=60,
    about=(
        "I'm the Harbourview Bakery assistant. I can help with our hours and location, our menu "
        "and prices, custom and wedding cakes, and holiday orders. For anything else, give the "
        "bakery a call."
    ),
    page_links=(
        (1, "Visit us", "https://bakery.pooya.website/visit/"),
        (2, "See our menu", "https://bakery.pooya.website/menu/"),
        (3, "Order a custom cake", "https://bakery.pooya.website/custom-cakes/"),
        (4, "Holiday order guide", "https://bakery.pooya.website/holiday-order-guide/"),
    ),
)

BOTS: dict[str, Bot] = {
    NORTHWIND.id: NORTHWIND,
    KINGSWAY_BOT.id: KINGSWAY_BOT,
    HARBOURVIEW.id: HARBOURVIEW,
}


@dataclass
class LoadedBot:
    bot: Bot
    document: Document


@dataclass
class BotRegistry:
    """Bots with their knowledge bases ingested and pinned in memory."""

    bots: dict[str, LoadedBot] = field(default_factory=dict)

    def get(self, bot_id: str) -> LoadedBot | None:
        return self.bots.get(bot_id)

    @classmethod
    def load(cls, bots: dict[str, Bot], settings: Settings) -> "BotRegistry":
        loaded: dict[str, LoadedBot] = {}
        # Upload limits are for visitors' files, not for the bots' own knowledge bases.
        settings = settings.model_copy(update={"max_pages": 10_000})
        for bot in bots.values():
            path = bot.knowledge_base
            bot_settings = settings
            if bot.chunk_words:
                bot_settings = settings.model_copy(
                    update={
                        "chunk_words": bot.chunk_words,
                        "chunk_overlap_words": min(
                            settings.chunk_overlap_words, bot.chunk_words // 4
                        ),
                    }
                )
            doc = ingest_pdf(path.name, path.read_bytes(), bot_settings, list(bot.suggestions))
            doc.id = f"bot-{bot.id}"
            loaded[bot.id] = LoadedBot(bot=bot, document=doc)
            logger.info("Loaded bot %s: %s pages, %s chunks", bot.id, doc.pages, len(doc.chunks))
        return cls(loaded)
