"""Routes a booking bot's messages: booking talk goes to the receptionist, the rest to the docs.

A message counts as booking talk when it is a widget tap, mentions booking or availability,
names a service and a day, or continues a booking already under way. Everything else is a
normal help-center answer with citations, so "Do you take cards?" still costs nothing when
the documents don't cover it.
"""

import logging
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

from app.answering import PROVIDER_DOWN_NOTICE, Answerer
from app.booking.base import BookingProvider, BookingUnavailableError
from app.bots import Bot
from app.limits import LiveQuota
from app.models import (
    AskRequest,
    BookingEvent,
    ChoicesEvent,
    DoneEvent,
    ErrorEvent,
    MetaEvent,
    StreamEvent,
    TextEvent,
    Turn,
)
from app.providers.base import ProviderError
from app.receptionist.claude import ClaudeReceptionist
from app.receptionist.desk import BookingDesk, DeskStore
from app.receptionist.intent import is_booking_message
from app.receptionist.offline import OfflineReceptionist
from app.settings import ProviderName
from app.store import SessionStore

logger = logging.getLogger(__name__)

Now = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class Receptionist:
    def __init__(
        self,
        *,
        answerer: Answerer,
        sessions: SessionStore,
        providers: dict[str, BookingProvider],
        quota: LiveQuota,
        llm: ClaudeReceptionist | None = None,
        fallback_to_mock: bool = True,
        now: Now = utc_now,
    ) -> None:
        self.answerer = answerer
        self.sessions = sessions
        self.providers = providers
        self.quota = quota
        self.llm = llm
        self.fallback_to_mock = fallback_to_mock
        self.now = now
        self.desks = DeskStore()

    def handles(self, bot: Bot) -> bool:
        return bot.booking is not None and bot.id in self.providers

    async def stream(
        self,
        bot: Bot,
        doc_id: str,
        body: AskRequest,
        *,
        client_ip: str,
        answer_docs: Callable[[], AsyncIterator[StreamEvent]],
    ) -> AsyncIterator[StreamEvent]:
        assert bot.booking is not None
        provider = self.providers[bot.id]
        state = self.desks.get(bot.id, body.session_id)
        state.turn += 1
        desk = BookingDesk(provider, state, self.now)
        question = body.question.strip()

        booking_turn = (
            body.action is not None
            or state.in_flow
            or is_booking_message(question, provider.catalog.services, desk.today)
        )
        if not booking_turn:
            async for event in answer_docs():
                yield event
            return

        offline = OfflineReceptionist(bot.business, bot.booking.phone)
        live_name: ProviderName = self.llm.name if self.llm else "mock"
        name: ProviderName = "mock"
        notice: str | None = None
        try:
            if body.action is not None:
                # Taps need no language model: handle them directly, whichever mode is on.
                name = live_name
                reply = await offline.handle_action(desk, body.action)
            elif self.llm is not None:
                reason = self.quota.take(client_ip)
                if reason and self.fallback_to_mock:
                    notice = reason
                    reply = await offline.handle_text(desk, question)
                else:
                    try:
                        history = self.sessions.history(doc_id, body.session_id)
                        system = self.llm.system_prompt(bot.name, bot.business, bot.booking.about)
                        state.last_booking_turn = state.turn
                        reply = await self.llm.reply(desk, question, history, system=system)
                        name = self.llm.name
                    except ProviderError as exc:
                        if not (exc.fallback_ok and self.fallback_to_mock):
                            yield MetaEvent(provider=self.llm.name)
                            yield ErrorEvent(code=exc.code, message=exc.message)
                            return
                        logger.warning("Receptionist fell back to offline mode (%s)", exc.code)
                        notice = PROVIDER_DOWN_NOTICE
                        reply = await offline.handle_text(desk, question)
            else:
                reply = await offline.handle_text(desk, question)
        except BookingUnavailableError:
            yield MetaEvent(provider=live_name)
            text = (
                "I can't reach our booking system right now, so I can't check times. "
                f"Please try again in a minute, or call us at {bot.booking.phone}."
            )
            yield TextEvent(text=text)
            self._remember(doc_id, body, question, text)
            yield DoneEvent(provider=live_name, grounded=False, citations=0, handoff=True)
            return
        except Exception:
            logger.exception("Receptionist failed")
            yield MetaEvent(provider=live_name)
            yield ErrorEvent(code="internal_error", message="Something went wrong on our side.")
            return

        yield MetaEvent(provider=name, notice=notice)
        text_parts: list[str] = []
        for event in reply:
            if isinstance(event, TextEvent):
                text_parts.append(event.text)
            yield event
        self._remember(doc_id, body, question, " ".join(text_parts), reply)
        yield DoneEvent(provider=name, grounded=False, citations=0, handoff=False)

    def _remember(
        self,
        doc_id: str,
        body: AskRequest,
        question: str,
        text: str,
        reply: list[TextEvent | ChoicesEvent | BookingEvent] | None = None,
    ) -> None:
        # Keep a note of what the widget showed, so a follow-up has the context.
        notes = []
        for event in reply or []:
            if isinstance(event, ChoicesEvent):
                notes.append(f"[{event.label}: {', '.join(o.label for o in event.options)}]")
            elif isinstance(event, BookingEvent):
                notes.append(f"[Booking {event.status}: {event.service}, {event.when}]")
        answer = " ".join([text, *notes]).strip()
        self.sessions.append(doc_id, body.session_id, Turn(question=question, answer=answer))
