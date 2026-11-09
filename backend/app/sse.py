"""Server-sent events framing."""

from collections.abc import AsyncIterator

from app.models import StreamEvent


def format_sse(event: StreamEvent) -> str:
    return f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"


async def sse_stream(events: AsyncIterator[StreamEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield format_sse(event)
