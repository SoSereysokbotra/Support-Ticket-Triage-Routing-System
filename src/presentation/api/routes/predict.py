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

        # Asynchronously log prediction telemetry for drift & KPI monitoring
        logger = getattr(request.app.state, "prediction_logger", None)
        if logger:
            try:
                logger.log_prediction(
                    ticket_id=response_dto.ticket_id,
                    text=payload.text,
                    predicted_category=response_dto.predicted_category,
                    confidence=response_dto.confidence,
                    latency_ms=response_dto.latency_ms,
                    probabilities=response_dto.probabilities,
                    customer_id=payload.customer_id,
                    customer_tier=response_dto.customer_features.get("customer_tier") if response_dto.customer_features else None,
                    is_vip=response_dto.customer_features.get("is_vip") if response_dto.customer_features else None,
                    model_version=response_dto.model_version,
                )
            except Exception:
                pass  # Non-blocking telemetry

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
    input_dtos = [
        TicketInputDTO(
            text=item.text,
            title=item.title,
            customer_id=item.customer_id,
            urgency_hint=item.urgency_hint,
        )
        for item in payload.tickets
    ]

    try:
        response_dtos = use_case.batch_execute(input_dtos)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {str(err)}")

    results = []
    log_records = []

    for item, response_dto in zip(payload.tickets, response_dtos):
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
        log_records.append({
            "ticket_id": response_dto.ticket_id,
            "text": item.text,
            "predicted_category": response_dto.predicted_category,
            "confidence": response_dto.confidence,
            "probabilities": response_dto.probabilities,
            "latency_ms": response_dto.latency_ms,
            "customer_id": item.customer_id,
            "customer_tier": response_dto.customer_features.get("customer_tier") if response_dto.customer_features else None,
            "is_vip": response_dto.customer_features.get("is_vip") if response_dto.customer_features else None,
            "model_version": response_dto.model_version,
        })

    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

    # Batch telemetry logging
    logger = getattr(request.app.state, "prediction_logger", None)
    if logger and log_records:
        try:
            logger.log_batch(log_records)
        except Exception:
            pass

    return TicketPredictBatchResponse(
        results=results,
        total_latency_ms=round(total_latency_ms, 2),
        batch_size=len(results),
    )
