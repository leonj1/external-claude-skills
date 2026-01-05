"""FastAPI handlers for skill routing endpoints."""
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lib.skill_router.service import SkillRoutingService, RouteResponse


class RouteRequest(BaseModel):
    """Request body for the /route endpoint."""
    query: str


class RouteResponseModel(BaseModel):
    """Response model for the /route endpoint."""
    matched_task: str | None
    skills: list[str]
    execution_order: list[str]
    route_type: str
    tier: int
    confidence: float


def create_app(manifest_path: str) -> FastAPI:
    """Create a FastAPI application with skill routing endpoints.

    Args:
        manifest_path: Path to the manifest YAML file

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(title="Skill Router API", version="0.1.0")
    service = SkillRoutingService(manifest_path)

    @app.post("/route", response_model=RouteResponseModel)
    def route_query(request: RouteRequest) -> RouteResponseModel:
        """Route a user query to the appropriate skills."""
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        response = service.route(request.query)
        return RouteResponseModel(
            matched_task=response.matched_task,
            skills=response.skills,
            execution_order=response.execution_order,
            route_type=response.route_type,
            tier=response.tier,
            confidence=response.confidence,
        )

    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


def create_app_from_env() -> FastAPI:
    """Factory function for uvicorn that reads manifest path from environment."""
    manifest_path = os.environ.get("MANIFEST_PATH", "/app/manifest.yaml")
    return create_app(manifest_path)
