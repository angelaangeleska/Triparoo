from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.core.exceptions import AppException, NotFoundError
from app.models.user import User
from app.schemas.trip_planner import (
    BudgetOptimizeRequest,
    BudgetOptimizeResponse,
    CheapestDatesRequest,
    CheapestDatesResponse,
    CheapestDestinationsRequest,
    CheapestDestinationsResponse,
    ChildActivitiesRequest,
    ChildActivitiesResponse,
    ItineraryRequest,
    ItineraryResponse,
    RecommendRequest,
    RecommendResponse,
    ResolvedOriginRead,
)
from app.services.budget_service import BudgetOptimizationService
from app.services.itinerary_service import ChildActivityService, ItineraryService
from app.services.origin_resolver import OriginResolverService
from app.services.trip_planner_service import TripPlannerService

router = APIRouter(prefix="/trip-planner", tags=["Trip Planner"])


@router.get("/resolve-origin", response_model=ResolvedOriginRead)
async def resolve_origin(
    q: str = Query(min_length=2, description="City or country name"),
    session=Depends(get_db),
):
    service = OriginResolverService(session)
    resolved = await service.resolve(q)
    if not resolved:
        raise NotFoundError(f"Could not resolve location: {q}")
    return ResolvedOriginRead(
        query=resolved.query,
        location_type=resolved.location_type,
        display_name=resolved.display_name,
        primary_airport_id=resolved.primary_airport_id,
        airport_count=len(resolved.airport_ids),
        message=resolved.message,
    )


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    payload: RecommendRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = TripPlannerService(session)
        return await service.recommend(payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/cheapest-destinations", response_model=CheapestDestinationsResponse)
async def cheapest_destinations(
    payload: CheapestDestinationsRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = TripPlannerService(session)
        return await service.cheapest_destinations(payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/cheapest-dates", response_model=CheapestDatesResponse)
async def cheapest_dates(
    payload: CheapestDatesRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = TripPlannerService(session)
        return await service.cheapest_dates(payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/itinerary", response_model=ItineraryResponse)
async def itinerary(
    payload: ItineraryRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = ItineraryService(session)
        return await service.generate(payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/child-activities", response_model=ChildActivitiesResponse)
async def child_activities(
    payload: ChildActivitiesRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = ChildActivityService(session)
        return await service.recommend(payload)
    except AppException as exc:
        raise handle_app_exception(exc)


@router.post("/budget-optimize", response_model=BudgetOptimizeResponse)
async def budget_optimize(
    payload: BudgetOptimizeRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = BudgetOptimizationService(session)
        return await service.optimize(payload)
    except AppException as exc:
        raise handle_app_exception(exc)
