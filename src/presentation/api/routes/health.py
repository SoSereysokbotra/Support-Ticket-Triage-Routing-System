import time
import torch
from fastapi import APIRouter, Request

from src.presentation.api.schemas.ticket_schema import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    start_time = getattr(request.app.state, "start_time", time.time())
    classifier = getattr(request.app.state, "classifier", None)

    model_version = classifier.model_version if classifier else "unloaded"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    uptime = time.time() - start_time

    return HealthResponse(
        status="healthy" if classifier else "degraded",
        model_version=model_version,
        device=device,
        uptime_seconds=round(uptime, 2),
    )
