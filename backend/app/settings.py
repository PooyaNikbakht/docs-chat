"""Application settings, read from environment variables (and an optional .env file)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["anthropic", "openai", "mock"]

# Values applied when PUBLIC_DEMO=true, unless the variable is set explicitly.
PUBLIC_DEMO_PRESET: dict[str, int] = {
    "max_upload_mb": 5,
    "max_pages": 25,
    "live_questions_per_ip_per_hour": 10,
    "live_questions_per_day": 300,
    "document_ttl_seconds": 3600,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Provider selection. Empty means: pick by available key, else mock.
    llm_provider: Literal["anthropic", "openai", "offline", "mock", ""] = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    anthropic_max_tokens: int = 4096
    openai_api_key: str = ""
    openai_model: str = ""
    provider_timeout_seconds: float = 30.0

    # HTTP
    # Origins allowed on upload and document routes. Bot routes use each bot's own list.
    cors_origins: str = "http://localhost:3010"
    # Where the sample site lives, for links such as the bot's "Talk to a human" page.
    public_site_url: str = "http://localhost:3010"
    trust_proxy_headers: bool = False

    # Upload limits
    max_upload_mb: int = 20
    max_pages: int = 300
    min_chars_per_page: int = 40

    # Chunking and retrieval
    chunk_words: int = 400
    chunk_overlap_words: int = 60
    top_k: int = 6
    min_retrieval_score: float = 1.0
    # A live model says "not found" itself, so it only needs the question to share a word with
    # the document. Off-topic questions score 0 and still never reach the model.
    live_min_retrieval_score: float = 0.1
    # A document this short goes to a live model whole when keywords find nothing ("products"
    # when the help center says "menu"); the model decides whether it answers the question.
    whole_document_max_words: int = 3000

    # Conversation
    history_turns: int = 6

    # Abuse and cost controls
    ask_rate_limit_per_minute: int = 20
    live_questions_per_ip_per_hour: int = 0  # 0 means no cap
    live_questions_per_day: int = 0  # 0 means no cap
    fallback_to_mock: bool = True
    document_ttl_seconds: int = 0  # 0 means keep until restart
    max_documents: int = 200

    # Booking receptionist. `mock` uses the built-in weekly schedule; `http` calls the
    # business's booking system at BOOKING_API_URL (see app/booking/http.py).
    booking_provider: Literal["mock", "http"] = "mock"
    booking_api_url: str = ""
    booking_timeout_seconds: float = 8.0
    # How many tool rounds Claude may take for one booking message.
    booking_max_tool_rounds: int = 6

    # Mock adapter pacing, so the stream looks like a stream.
    mock_delay_seconds: float = 0.012

    public_demo: bool = Field(default=False)

    @model_validator(mode="after")
    def _apply_public_preset(self) -> Self:
        if self.public_demo:
            for name, value in PUBLIC_DEMO_PRESET.items():
                if name not in self.model_fields_set:
                    setattr(self, name, value)
        return self

    @property
    def provider(self) -> ProviderName:
        """The active provider, following the shared rules in STANDARDS.md."""
        if self.llm_provider in ("offline", "mock"):
            return "mock"
        if self.llm_provider in ("anthropic", "openai"):
            return self.llm_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "mock"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
