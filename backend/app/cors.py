"""CORS per route: bot routes follow each bot's allowed origins, everything else allows
only the frontend origin.

The demo bot allows any origin so the embed works on any site; rate limits and the live
answer caps protect it instead.
"""

import re

from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

BOT_PATH = re.compile(r"^/bots/(?P<bot_id>[^/]+)(?:/ask)?/?$")
METHODS = ["GET", "POST"]
HEADERS = ["Content-Type"]


class RouteCORSMiddleware:
    def __init__(
        self, app: ASGIApp, default_origins: list[str], bot_origins: dict[str, list[str]]
    ) -> None:
        self.default = CORSMiddleware(
            app, allow_origins=default_origins, allow_methods=METHODS, allow_headers=HEADERS
        )
        self.bots = {
            bot_id: CORSMiddleware(
                app, allow_origins=origins, allow_methods=METHODS, allow_headers=HEADERS
            )
            for bot_id, origins in bot_origins.items()
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        handler = self.default
        if scope["type"] == "http":
            match = BOT_PATH.match(scope["path"])
            if match:
                handler = self.bots.get(match["bot_id"], self.default)
        await handler(scope, receive, send)
