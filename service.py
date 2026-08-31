"""
BentoML Multi-Model Service
Exposes low-latency batched REST/gRPC endpoints for Support Ticket Triage & Routing.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import bentoml
from pydantic import BaseModel, Field

from src.application.dto.ticket_dto import TicketInputDTO
from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter
from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier
from src.infrastructure.models.urgency_classifier import BaselineUrgencyClassifier
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry


class TicketRequestSchema(BaseModel):
    text: str = Field(..., min_length=5, description="Ticket text content")
    title: Optional[str] = Field(default=None, description="Optional ticket title")
    customer_id: Optional[str] = Field(default=None, description="Customer identifier for Feast feature join")
    urgency_hint: Optional[str] = Field(default=None, description="Manual urgency override (Low/Medium/High/Critical)")


class TicketResponseSchema(BaseModel):
    ticket_id: str
    predicted_category: str
    confidence: float
    assigned_team: str
    priority_level: str
    target_sla_hours: int
    auto_routed: bool
    routing_reason: str
    model_version: str
    latency_ms: float
    customer_features: Optional[Dict[str, Any]] = None


@bentoml.service(
    name="support_ticket_triage_service",
    resources={"cpu": "2"},
)
class SupportTicketTriageService:
    def __init__(self):
        # 1. Resolve production category model
        registry = MLflowModelRegistry()
        try:
            self.classifier = registry.load_model_by_version_or_alias(model_name="ticket-classifier", alias="production")
        except Exception:
            self.classifier = DistilBertTicketClassifier(model_version="distilbert-local-v0")

        # 2. Resolve urgency model
        self.urgency_classifier = BaselineUrgencyClassifier(model_version="tfidf-urgency-v0")
        try:
            from src.infrastructure.data.dataset_loader import DatasetLoader
            df = DatasetLoader().load_or_create_dataset(num_samples=300)
            self.urgency_classifier.fit(df["text"].tolist(), df["urgency"].tolist())
        except Exception:
            pass

        # 3. Feature store & routing
        self.feature_store = FeastFeatureStoreAdapter()
        self.use_case = PredictTicketUseCase(
            classifier=self.classifier,
            urgency_classifier=self.urgency_classifier,
            router=RouteTicketUseCase(),
            feature_store=self.feature_store,
        )

    @bentoml.api
    def predict(self, ticket: TicketRequestSchema) -> Dict[str, Any]:
        dto = TicketInputDTO(
            text=ticket.text,
            title=ticket.title,
            customer_id=ticket.customer_id,
            urgency_hint=ticket.urgency_hint,
        )
        res = self.use_case.execute(dto)
        return {
            "ticket_id": res.ticket_id,
            "predicted_category": res.predicted_category,
            "confidence": res.confidence,
            "assigned_team": res.assigned_team,
            "priority_level": res.priority_level,
            "target_sla_hours": res.target_sla_hours,
            "auto_routed": res.auto_routed,
            "routing_reason": res.routing_reason,
            "model_version": res.model_version,
            "latency_ms": res.latency_ms,
            "customer_features": res.customer_features,
        }

    @bentoml.api
    def predict_batch(self, tickets: List[TicketRequestSchema]) -> List[Dict[str, Any]]:
        results = []
        for t in tickets:
            results.append(self.predict(t))
        return results
