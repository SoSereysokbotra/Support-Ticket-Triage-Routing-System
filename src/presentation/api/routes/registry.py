from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.application.use_cases.predict_ticket import PredictTicketUseCase
from src.infrastructure.registry.mlflow_registry import MLflowModelRegistry

router = APIRouter(prefix="/api/v1/registry", tags=["Model Registry & Lifecycle"])


class PromoteRequest(BaseModel):
    version: str = Field(
        ...,
        description="The target model version number (e.g. '1', '2')",
        json_schema_extra={"example": "2"},
    )
    alias: str = Field(
        default="production",
        description="The alias tag to assign (e.g. 'production', 'staging', 'champion')",
        json_schema_extra={"example": "production"},
    )


class RollbackRequest(BaseModel):
    target_version: str = Field(
        ...,
        description="The stable model version number to rollback production to",
        json_schema_extra={"example": "1"},
    )


class RollbackResponse(BaseModel):
    model_name: str
    alias: str
    previous_version: Optional[str]
    current_version: str
    rollback_status: str
    reloaded_in_memory: bool


@router.get("/versions")
async def list_registered_versions(request: Request) -> Dict[str, Any]:
    registry: MLflowModelRegistry = getattr(request.app.state, "registry", None)
    if not registry:
        raise HTTPException(status_code=503, detail="MLflow registry is not initialized.")

    versions = registry.list_versions()
    prod_version = registry.get_version_by_alias(alias="production")
    staging_version = registry.get_version_by_alias(alias="staging")

    return {
        "model_name": "ticket-classifier",
        "active_production_version": str(prod_version.version) if prod_version else None,
        "active_staging_version": str(staging_version.version) if staging_version else None,
        "versions": versions,
    }


@router.post("/promote")
async def promote_model_version(
    payload: PromoteRequest,
    request: Request,
) -> Dict[str, Any]:
    registry: MLflowModelRegistry = getattr(request.app.state, "registry", None)
    if not registry:
        raise HTTPException(status_code=503, detail="MLflow registry is not initialized.")

    try:
        registry.set_alias(
            model_name="ticket-classifier",
            alias=payload.alias,
            version=payload.version,
        )

        # If promoting to production, auto hot-reload active classifier
        reloaded = False
        if payload.alias.lower() == "production":
            new_classifier = registry.load_model_by_version_or_alias(alias="production")
            request.app.state.classifier = new_classifier
            request.app.state.predict_use_case = PredictTicketUseCase(
                classifier=new_classifier,
                router=request.app.state.route_use_case,
            )
            reloaded = True

        return {
            "status": "success",
            "message": f"Successfully promoted ticket-classifier version v{payload.version} to alias '{payload.alias}'",
            "version": payload.version,
            "alias": payload.alias,
            "reloaded_in_memory": reloaded,
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to promote model version: {str(err)}")


@router.post("/rollback", response_model=RollbackResponse)
async def rollback_production_model(
    payload: RollbackRequest,
    request: Request,
) -> RollbackResponse:
    registry: MLflowModelRegistry = getattr(request.app.state, "registry", None)
    if not registry:
        raise HTTPException(status_code=503, detail="MLflow registry is not initialized.")

    try:
        rollback_info = registry.rollback_to_version(target_version=payload.target_version)

        # Hot-reload in memory to immediately serve the rolled back version
        new_classifier = registry.load_model_by_version_or_alias(version=payload.target_version)
        request.app.state.classifier = new_classifier
        request.app.state.predict_use_case = PredictTicketUseCase(
            classifier=new_classifier,
            router=request.app.state.route_use_case,
        )

        return RollbackResponse(
            model_name=rollback_info["model_name"],
            alias=rollback_info["alias"],
            previous_version=rollback_info["previous_version"],
            current_version=rollback_info["current_version"],
            rollback_status="success",
            reloaded_in_memory=True,
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(err)}")


@router.post("/reload")
async def reload_production_model(request: Request) -> Dict[str, Any]:
    registry: MLflowModelRegistry = getattr(request.app.state, "registry", None)
    if not registry:
        raise HTTPException(status_code=503, detail="MLflow registry is not initialized.")

    try:
        new_classifier = registry.load_model_by_version_or_alias(alias="production")
        request.app.state.classifier = new_classifier
        request.app.state.predict_use_case = PredictTicketUseCase(
            classifier=new_classifier,
            router=request.app.state.route_use_case,
        )
        return {
            "status": "success",
            "message": "Hot-reloaded current production model from registry into memory.",
            "loaded_model_version": new_classifier.model_version,
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(err)}")
