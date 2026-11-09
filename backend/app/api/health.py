from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import Services, get_services
from app.models import HealthOut, LimitsOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(services: Annotated[Services, Depends(get_services)]) -> HealthOut:
    s = services.settings
    provider = s.provider
    model = {"anthropic": s.anthropic_model, "openai": s.openai_model}.get(provider)
    return HealthOut(
        provider=provider,
        model=model,
        public_demo=s.public_demo,
        limits=LimitsOut(
            max_upload_mb=s.max_upload_mb,
            max_pages=s.max_pages,
            document_ttl_minutes=(s.document_ttl_seconds // 60) or None,
        ),
    )
