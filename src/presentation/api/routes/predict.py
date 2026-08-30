import time
from fastapi import APIRouter, HTTPException, Request

from src.application.dto.ticket_dto import TicketInputDTO
from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.presentation.api.schemas.ticket_schema import (
    TicketPredictBatchRequest,
    TicketPredictBatchResponse,
    TicketPredictRequest,
    TicketPredictResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Triage & Routing"])


@router.post("/predict", response_model=TicketPredictResponse)
async def predict_ticket(
    payload: TicketPredictRequest,
    request: Request,
) -> TicketPredictResponse:
    use_case: PredictTicketUseCase = getattr(request.app.state, "predict_use_case", None)
    if not use_case:
        raise HTTPException(status_code=503, detail="Predict use case is not initialized.")

    try:
        dto = TicketInputDTO(
            text=payload.text,
            title=payload.title,
            customer_id=payload.customer_id,
            urgency_hint=payload.urgency_hint,
        )
        response_dto = use_case.execute(dto)

        return TicketPredictResponse(
            ticket_id=response_dto.ticket_id,
            predicted_category=response_dto.predicted_category,
            confidence=response_dto.confidence,
            probabilities=response_dto.probabilities,
            assigned_team=response_dto.assigned_team,
            priority_level=response_dto.priority_level,
            target_sla_hours=response_dto.target_sla_hours,
            auto_routed=response_dto.auto_routed,
            routing_reason=response_dto.routing_reason,
            model_version=response_dto.model_version,
            latency_ms=response_dto.latency_ms,
            customer_features=response_dto.customer_features,
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {str(err)}")


@router.post("/predict/batch", response_model=TicketPredictBatchResponse)
async def predict_ticket_batch(
    payload: TicketPredictBatchRequest,
    request: Request,
) -> TicketPredictBatchResponse:
    use_case: PredictTicketUseCase = getattr(request.app.state, "predict_use_case", None)
    if not use_case:
        raise HTTPException(status_code=503, detail="Predict use case is not initialized.")

    start_time = time.perf_counter()
    results = []

    for item in payload.tickets:
        dto = TicketInputDTO(
            text=item.text,
            title=item.title,
            customer_id=item.customer_id,
            urgency_hint=item.urgency_hint,
        )
        response_dto = use_case.execute(dto)
        results.append(
            TicketPredictResponse(
                ticket_id=response_dto.ticket_id,
                predicted_category=response_dto.predicted_category,
                confidence=response_dto.confidence,
                probabilities=response_dto.probabilities,
                assigned_team=response_dto.assigned_team,
                priority_level=response_dto.priority_level,
                target_sla_hours=response_dto.target_sla_hours,
                auto_routed=response_dto.auto_routed,
                routing_reason=response_dto.routing_reason,
                model_version=response_dto.model_version,
                latency_ms=response_dto.latency_ms,
                customer_features=response_dto.customer_features,
            )
        )

    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

    return TicketPredictBatchResponse(
        results=results,
        total_latency_ms=round(total_latency_ms, 2),
        batch_size=len(results),
    )
