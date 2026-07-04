import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
from app.integrations.accommodations.base import AccommodationSearchCriteria
from app.integrations.accommodations.factory import get_accommodation_provider
from app.integrations.accommodations.serialize import accommodation_to_dict
from app.models.user import User
from app.schemas.ai_guide import AITripGuideRequest, AITripGuideResponse
from app.schemas.trip_planner import (
    AccommodationSummary,
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
from app.services.ai_trip_guide_service import AITripGuideService
from app.services.budget_service import BudgetOptimizationService
from app.services.itinerary_service import ChildActivityService, ItineraryService
from app.services.origin_resolver import OriginResolverService
from app.services.trip_planner_service import TripPlannerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trip-planner", tags=["Trip Planner"])


@router.get("/hotels", response_model=list[AccommodationSummary])
async def search_hotels(
    city: str = Query(description="City name, e.g. Prague"),
    check_in: date = Query(description="Check-in date YYYY-MM-DD"),
    check_out: date = Query(description="Check-out date YYYY-MM-DD"),
    adults: int = Query(default=2, ge=1),
    children: int = Query(default=0, ge=0),
    country: str = Query(default="", description="Country name for more accurate results"),
):
    if not (settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET):
        raise HTTPException(
            status_code=503,
            detail="Hotel search is not configured (missing AMADEUS_CLIENT_ID/AMADEUS_CLIENT_SECRET)",
        )

    provider = get_accommodation_provider()
    try:
        offers = await provider.search(
            AccommodationSearchCriteria(
                city=city,
                check_in=check_in,
                check_out=check_out,
                adults=adults,
                children=children,
                country=country,
            )
        )
        summaries = [AccommodationSummary.from_dict(accommodation_to_dict(o)) for o in offers]
        return [s for s in summaries if s]
    except Exception as exc:
        logger.exception("Hotel search failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/resolve-origin", response_model=ResolvedOriginRead)
async def resolve_origin(
    q: str = Query(min_length=2, description="City, country, or city + country (e.g. Rome, Italy)"),
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
    user: User = Depends(get_current_user),
):
    try:
        service = TripPlannerService(session)
        return await service.recommend(payload, user.id)
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


@router.post("/ai-guide", response_model=AITripGuideResponse)
async def ai_trip_guide(
    payload: AITripGuideRequest,
    session=Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        service = AITripGuideService(session)
        return await service.generate(payload)
    except AppException as exc:
        raise handle_app_exception(exc)
