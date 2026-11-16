"""Versioned API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import agents, components, projects

api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(components.router)
api_router.include_router(agents.router)
