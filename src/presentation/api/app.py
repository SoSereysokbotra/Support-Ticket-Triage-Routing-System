import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.application.use_cases.route_ticket import RouteTicketUseCase
from src.infrastructure.data.dataset_loader import DatasetLoader
from src.infrastructure.features.feast_store import FeastFeatureStoreAdapter
from src.infrastructure.models.baseline_classifier import BaselineTfidfClassifier
from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier
from src.infrastructure.monitoring.prediction_logger import PredictionLogger
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry
from src.presentation.api.routes.health import router as health_router
from src.presentation.api.routes.monitoring import router as monitoring_router
from src.presentation.api.routes.predict import router as predict_router
from src.presentation.api.routes.registry import router as registry_router


def create_app(model_override=None, registry_override=None, logger_override=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.start_time = time.time()
        project_root = Path(__file__).resolve().parents[3]

        registry = registry_override or MLflowModelRegistry(project_root=project_root)
        app.state.registry = registry

        # Initialize Prediction Logger
        if logger_override:
            app.state.prediction_logger = logger_override
        elif not getattr(app.state, "prediction_logger", None):
            prediction_logger = PredictionLogger(db_path=project_root / "data" / "monitoring" / "inference_logs.db")
            app.state.prediction_logger = prediction_logger

        if model_override:
            classifier = model_override
        else:
            # 1. Try loading production model from MLflow Model Registry
            classifier = None
            try:
                prod_version = registry.get_version_by_alias(alias="production")
                if prod_version:
                    print(f"[Lifespan] Loading production model v{prod_version.version} from MLflow Model Registry...")
                    classifier = registry.load_model_by_version_or_alias(alias="production")
            except Exception as e:
                print(f"[Lifespan] MLflow production model load skipped/failed: {e}")

            # 2. Fallback to local DistilBERT checkpoint if present
            if not classifier:
                distilbert_path = project_root / "models" / "distilbert_v0"
                if distilbert_path.exists() and (distilbert_path / "config.json").exists():
                    print(f"[Lifespan] Loading local DistilBERT from {distilbert_path}...")
                    classifier = DistilBertTicketClassifier(
                        model_path_or_name=distilbert_path,
                        model_version="distilbert-local-v0",
                    )

            # 3. Fallback to TF-IDF Baseline
            if not classifier:
                print("[Lifespan] No checkpoint/registry model found. Fitting TF-IDF Baseline model...")
                loader = DatasetLoader()
                df = loader.load_or_create_dataset()
                classifier = BaselineTfidfClassifier(model_version="tfidf-baseline-v0")
                classifier.fit(df["text"].tolist(), df["category"].tolist())

        # 4. Initialize Urgency Model
        urgency_classifier = None
        try:
            urg_version = registry.get_version_by_alias(model_name="ticket-urgency-classifier", alias="production")
            if urg_version:
                print(f"[Lifespan] Loading production urgency model v{urg_version.version} from MLflow...")
                urgency_classifier = registry.load_model_by_version_or_alias(model_name="ticket-urgency-classifier", alias="production")
        except Exception:
            pass

        if not urgency_classifier:
            print("[Lifespan] Initializing baseline urgency classifier...")
            loader = DatasetLoader()
            df = loader.load_or_create_dataset()
            from src.infrastructure.models.urgency_classifier import BaselineUrgencyClassifier
            urgency_classifier = BaselineUrgencyClassifier(model_version="tfidf-urgency-v0")
            urgency_classifier.fit(df["text"].tolist(), df["urgency"].tolist())

        # Initialize Feast Feature Store
        feature_store = FeastFeatureStoreAdapter(repo_path=project_root / "features")
        app.state.feature_store = feature_store

        app.state.classifier = classifier
        app.state.urgency_classifier = urgency_classifier
        app.state.route_use_case = RouteTicketUseCase()
        app.state.predict_use_case = PredictTicketUseCase(
            classifier=classifier,
            urgency_classifier=urgency_classifier,
            router=app.state.route_use_case,
            feature_store=feature_store,
        )
        print(f"[Lifespan] System initialized with category model: {classifier.model_version}, urgency model: {urgency_classifier.model_version}")

        yield

        print("[Lifespan] Application shutting down...")

    app = FastAPI(
        title="Support Ticket Triage & Routing System",
        description="Production MLOps Service with Drift Monitoring & Automated Quality Gating",
        version="0.3.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(predict_router)
    app.include_router(registry_router)
    app.include_router(monitoring_router)

    return app


app = create_app()
