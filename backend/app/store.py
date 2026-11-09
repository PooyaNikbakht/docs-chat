"""In-memory storage for documents and conversation history.

Swap these for Postgres/pgvector, Redis or S3 in production (see the README).
"""

import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable

from app.models import Document, Turn

Clock = Callable[[], float]


class DocumentStore:
    """Documents by id, with an optional time-to-live and a size cap (oldest evicted)."""

    def __init__(
        self, ttl_seconds: int = 0, max_items: int = 200, clock: Clock = time.time
    ) -> None:
        self.ttl = ttl_seconds
        self.max_items = max_items
        self.clock = clock
        self._docs: OrderedDict[str, Document] = OrderedDict()
        self._lock = threading.Lock()

    def add(self, doc: Document) -> None:
        with self._lock:
            self._purge()
            self._docs[doc.id] = doc
            while len(self._docs) > self.max_items:
                self._docs.popitem(last=False)

    def get(self, doc_id: str) -> Document | None:
        with self._lock:
            self._purge()
            return self._docs.get(doc_id)

    def _purge(self) -> None:
        if self.ttl <= 0:
            return
        cutoff = self.clock() - self.ttl
        for doc_id in [d.id for d in self._docs.values() if d.created_at < cutoff]:
            del self._docs[doc_id]


class SessionStore:
    """The last N question and answer turns per (document, session)."""

    def __init__(self, max_turns: int = 6, max_sessions: int = 2000) -> None:
        self.max_turns = max_turns
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[tuple[str, str], deque[Turn]] = OrderedDict()
        self._lock = threading.Lock()

    def history(self, doc_id: str, session_id: str) -> list[Turn]:
        with self._lock:
            return list(self._sessions.get((doc_id, session_id), ()))

    def append(self, doc_id: str, session_id: str, turn: Turn) -> None:
        with self._lock:
            key = (doc_id, session_id)
            turns = self._sessions.setdefault(key, deque(maxlen=self.max_turns))
            turns.append(turn)
            self._sessions.move_to_end(key)
            while len(self._sessions) > self.max_sessions:
                self._sessions.popitem(last=False)
