from app.limits import DailyCap, LiveQuota, SlidingWindowLimiter
from app.models import Document, Turn
from app.store import DocumentStore, SessionStore


class Clock:
    def __init__(self, t: float = 1_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def test_sliding_window():
    clock = Clock()
    limiter = SlidingWindowLimiter(2, 60, clock)
    assert limiter.hit("ip") and limiter.hit("ip")
    assert not limiter.hit("ip")
    assert limiter.hit("other")
    assert limiter.retry_after("ip") > 0
    clock.t += 61
    assert limiter.hit("ip")


def test_zero_limit_disables():
    assert all(SlidingWindowLimiter(0, 60).hit("x") for _ in range(100))
    assert all(DailyCap(0).take() for _ in range(100))


def test_daily_cap_resets_each_utc_day():
    clock = Clock(0)
    cap = DailyCap(1, clock)
    assert cap.take() and not cap.take()
    clock.t += 86_400
    assert cap.take()


def test_live_quota_reasons():
    quota = LiveQuota(per_ip_per_hour=1, per_day=2, clock=Clock())
    assert quota.take("a") is None
    assert "hourly" in (quota.take("a") or "")
    assert quota.take("b") is None
    assert "daily" in (quota.take("c") or "")


def test_document_ttl_and_cap():
    clock = Clock()
    store = DocumentStore(ttl_seconds=3600, max_items=2, clock=clock)
    for i in range(3):
        store.add(Document(id=str(i), name="x", pages=1, chunks=[], created_at=clock.t))
    assert store.get("0") is None  # evicted by the size cap
    assert store.get("2") is not None
    clock.t += 3601
    assert store.get("2") is None  # expired


def test_session_keeps_last_turns():
    sessions = SessionStore(max_turns=6)
    for i in range(8):
        sessions.append("d", "s", Turn(f"q{i}", f"a{i}"))
    history = sessions.history("d", "s")
    assert [t.question for t in history] == [f"q{i}" for i in range(2, 8)]
    assert sessions.history("d", "other") == []
