from src.presentation.api.routes.health import router as health_router
from src.presentation.api.routes.predict import router as predict_router
from src.presentation.api.routes.registry import router as registry_router

__all__ = ["health_router", "predict_router", "registry_router"]
