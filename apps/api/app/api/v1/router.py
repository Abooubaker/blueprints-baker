"""Versioned API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import agents, build, components, electrical, projects

api_router = APIRouter()
api_router.include_router(build.router)
api_router.include_router(projects.router)
api_router.include_router(components.router)
api_router.include_router(agents.router)
api_router.include_router(electrical.router)
