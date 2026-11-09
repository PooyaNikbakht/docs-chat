"""FastAPI application factory."""

import logging

from fastapi import FastAPI

from app.answering import Answerer
from app.api import ask, documents, health
from app.api import bots as bot_routes
from app.api.deps import Services
from app.booking import BookingProvider, build_booking_provider
from app.bots import BOTS, Bot, BotRegistry
from app.cors import RouteCORSMiddleware
from app.errors import install_error_handlers
from app.limits import LiveQuota, SlidingWindowLimiter
from app.providers import AnswerProvider, build_provider
from app.providers.mock import MockProvider
from app.receptionist.claude import ClaudeReceptionist
from app.receptionist.service import Receptionist
from app.settings import Settings, get_settings
from app.store import DocumentStore, SessionStore


def create_app(
    settings: Settings | None = None,
    provider: AnswerProvider | None = None,
    bots: dict[str, Bot] | None = None,
    booking_providers: dict[str, BookingProvider] | None = None,
    receptionist_llm: ClaudeReceptionist | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    bots = BOTS if bots is None else bots
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    app = FastAPI(
        title="docs-chat API",
        version="0.2.0",
        description=(
            "Website support bots that answer from a business's documents. Answers stream "
            "with page-level citations, and say so when the documents don't cover a question."
        ),
    )
    app.add_middleware(
        RouteCORSMiddleware,
        default_origins=settings.cors_origin_list,
        bot_origins={bot.id: list(bot.allowed_origins) for bot in bots.values()},
    )
    install_error_handlers(app)

    fallback = MockProvider(delay_seconds=settings.mock_delay_seconds)
    active = provider or (fallback if settings.provider == "mock" else build_provider(settings))
    quota = LiveQuota(settings.live_questions_per_ip_per_hour, settings.live_questions_per_day)
    sessions = SessionStore(settings.history_turns)
    answerer = Answerer(
        active,
        fallback,
        quota,
        top_k=settings.top_k,
        min_score=settings.min_retrieval_score,
        live_min_score=settings.live_min_retrieval_score,
        whole_document_max_words=settings.whole_document_max_words,
        fallback_to_mock=settings.fallback_to_mock,
    )
    if booking_providers is None:
        booking_providers = {
            bot.id: build_booking_provider(settings, bot.booking.business, bot.booking.catalog)
            for bot in bots.values()
            if bot.booking is not None
        }
    if receptionist_llm is None and provider is None and settings.provider == "anthropic":
        receptionist_llm = build_receptionist_llm(settings)
    app.state.services = Services(
        settings=settings,
        documents=DocumentStore(settings.document_ttl_seconds, settings.max_documents),
        sessions=sessions,
        answerer=answerer,
        ask_limiter=SlidingWindowLimiter(settings.ask_rate_limit_per_minute, 60),
        bots=BotRegistry.load(bots, settings),
        receptionist=Receptionist(
            answerer=answerer,
            sessions=sessions,
            providers=booking_providers,
            quota=quota,
            llm=receptionist_llm,
            fallback_to_mock=settings.fallback_to_mock,
        ),
    )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(ask.router)
    app.include_router(bot_routes.router)
    return app


def build_receptionist_llm(settings: Settings) -> ClaudeReceptionist:
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=settings.anthropic_api_key or None,
        timeout=settings.provider_timeout_seconds,
        max_retries=1,
    )
    return ClaudeReceptionist(
        client,
        model=settings.anthropic_model,
        effort=settings.anthropic_effort,
        max_tokens=settings.anthropic_max_tokens,
        max_rounds=settings.booking_max_tool_rounds,
    )


app = create_app()
