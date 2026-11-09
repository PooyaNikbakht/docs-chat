from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.ask import ASK_RESPONSES, SSE_DESCRIPTION, check_rate, docs_events, sse_response
from app.api.deps import Services, get_services
from app.bots import LoadedBot, resolve_url
from app.errors import AppError
from app.models import AskRequest, BotOut, ErrorResponse, PageLink

router = APIRouter(prefix="/bots", tags=["bots"])


def _loaded(services: Services, bot_id: str) -> LoadedBot:
    loaded = services.bots.get(bot_id)
    if loaded is None:
        raise AppError(404, "not_found", "That bot doesn't exist.")
    return loaded


@router.get("/{bot_id}", response_model=BotOut, responses={404: {"model": ErrorResponse}})
def get_bot(bot_id: str, services: Annotated[Services, Depends(get_services)]) -> BotOut:
    """Public widget config: name, greeting, suggestions, colour and the human handoff."""
    bot = _loaded(services, bot_id).bot
    return BotOut(
        id=bot.id,
        name=bot.name,
        business=bot.business,
        subline=bot.subline,
        greeting=bot.greeting,
        suggestions=list(bot.suggestions),
        accent_color=bot.accent_color,
        handoff_text=bot.handoff_text,
        handoff_url=bot.resolve_handoff(services.settings.public_site_url),
        tooltip=bot.tooltip,
        source_label=bot.source_label,
        mode="demo" if services.settings.provider == "mock" else "live",
        booking=services.receptionist.handles(bot),
        show_sources=bot.show_sources,
        page_links=[
            PageLink(
                page=page, label=label, url=resolve_url(url, services.settings.public_site_url)
            )
            for page, label, url in bot.page_links
        ],
    )


@router.post(
    "/{bot_id}/ask",
    response_class=StreamingResponse,
    description=SSE_DESCRIPTION,
    responses=ASK_RESPONSES,
)
async def ask_bot(
    bot_id: str,
    body: AskRequest,
    request: Request,
    services: Annotated[Services, Depends(get_services)],
) -> StreamingResponse:
    loaded = _loaded(services, bot_id)
    bot, doc = loaded.bot, loaded.document
    if body.action is not None and not services.receptionist.handles(bot):
        raise AppError(400, "invalid", "This bot doesn't take bookings.")
    ip = check_rate(services, request)
    if not services.receptionist.handles(bot):
        return sse_response(docs_events(services, doc, body, bot.persona, ip))
    events = services.receptionist.stream(
        bot,
        doc.id,
        body,
        client_ip=ip,
        answer_docs=lambda: docs_events(services, doc, body, bot.persona, ip),
    )
    return sse_response(events)
