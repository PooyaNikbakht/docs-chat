from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import Services, client_ip, get_services
from app.errors import AppError
from app.models import AskRequest, Document, ErrorResponse, StreamEvent, Turn
from app.providers.base import DOCUMENT_PERSONA, Persona
from app.sse import sse_stream

router = APIRouter(tags=["ask"])

SSE_DESCRIPTION = """Streams server-sent events, in this order:

- `meta` `{provider, notice}`: which provider is answering (and why, if it fell back to demo mode)
- `text` `{text}`: answer text deltas
- `citation` `{index, chunk_id, page, quote, context}`: a source for the text just before it
- `choices` `{kind, label, options}`: tappable services, days or open times (booking bots)
- `booking` `{status, service, when, staff, name, contact, price, reference}`: a booking \
waiting for the visitor to confirm (`pending`) or written (`confirmed`)
- `done` `{provider, grounded, citations, handoff}` or `error` `{code, message}`
"""

ASK_RESPONSES: dict[int | str, dict] = {
    200: {"content": {"text/event-stream": {}}},
    404: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
}


def check_rate(services: Services, request: Request) -> str:
    """The caller's IP, after counting this question against the per-IP rate limit."""
    ip = client_ip(request, services.settings.trust_proxy_headers)
    if not services.ask_limiter.hit(ip):
        wait = services.ask_limiter.retry_after(ip)
        raise AppError(429, "rate_limited", f"Too many questions. Try again in {wait} seconds.")
    return ip


def docs_events(
    services: Services, doc: Document, body: AskRequest, persona: Persona, ip: str
) -> AsyncIterator[StreamEvent]:
    """A grounded answer about `doc`, remembered in the session history."""
    question = body.question.strip()
    history = services.sessions.history(doc.id, body.session_id)

    def remember(answer: str) -> None:
        services.sessions.append(doc.id, body.session_id, Turn(question=question, answer=answer))

    return services.answerer.stream(
        doc, question, history, client_ip=ip, remember=remember, persona=persona
    )


def sse_response(events: AsyncIterator[StreamEvent]) -> StreamingResponse:
    return StreamingResponse(
        sse_stream(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def answer_stream(
    services: Services,
    request: Request,
    doc: Document,
    body: AskRequest,
    persona: Persona,
) -> StreamingResponse:
    """Rate-limit, then stream a grounded answer about `doc` as server-sent events."""
    ip = check_rate(services, request)
    return sse_response(docs_events(services, doc, body, persona, ip))


@router.post(
    "/documents/{doc_id}/ask",
    response_class=StreamingResponse,
    description=SSE_DESCRIPTION,
    responses=ASK_RESPONSES,
)
async def ask(
    doc_id: str,
    body: AskRequest,
    request: Request,
    services: Annotated[Services, Depends(get_services)],
) -> StreamingResponse:
    doc = services.documents.get(doc_id)
    if doc is None:
        raise AppError(404, "not_found", "That document doesn't exist or has expired.")
    return answer_stream(services, request, doc, body, DOCUMENT_PERSONA)
