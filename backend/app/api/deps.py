"""Shared services, created once per app and reached through FastAPI dependencies."""

from dataclasses import dataclass

from fastapi import Request

from app.answering import Answerer
from app.bots import BotRegistry
from app.limits import SlidingWindowLimiter
from app.receptionist.service import Receptionist
from app.settings import Settings
from app.store import DocumentStore, SessionStore


@dataclass
class Services:
    settings: Settings
    documents: DocumentStore
    sessions: SessionStore
    answerer: Answerer
    ask_limiter: SlidingWindowLimiter
    bots: BotRegistry
    receptionist: Receptionist


def get_services(request: Request) -> Services:
    return request.app.state.services


def client_ip(request: Request, trust_proxy: bool) -> str:
    """The caller's IP. Behind a proxy we trust, use the last X-Forwarded-For hop."""
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if hops:
            return hops[-1]
    return request.client.host if request.client else "unknown"
