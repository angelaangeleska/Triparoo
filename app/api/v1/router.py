from fastapi import APIRouter

from app.api.v1 import auth, catalog, trip_planner

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(trip_planner.router)
api_router.include_router(catalog.router)
