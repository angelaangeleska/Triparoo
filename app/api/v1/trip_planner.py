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
from app.schemas.trip_planner import (
    AccommodationSummary,
    BookingSourceSummary,
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trip-planner", tags=["Trip Planner"])


def _to_accommodation_summary(data: dict) -> AccommodationSummary:
    sources = [BookingSourceSummary(**s) for s in (data.get("booking_sources") or [])]
    return AccommodationSummary(
        name=data.get("name", ""),
        type=data.get("type", ""),
        hotel_class=data.get("hotel_class", ""),
        rating=data.get("rating"),
        reviews_count=data.get("reviews_count"),
        price_per_night=data.get("price_per_night", 0.0),
        total_price=data.get("total_price", 0.0),
        currency=data.get("currency", "USD"),
        family_friendly=data.get("family_friendly", False),
        image_url=data.get("image_url", ""),
        google_url=data.get("google_url", ""),
        booking_sources=sources,
        amenities=data.get("amenities") or [],
        check_in_time=data.get("check_in_time", ""),
        check_out_time=data.get("check_out_time", ""),
        source=data.get("source", "serpapi"),
    )


@router.get("/hotels", response_model=list[AccommodationSummary])
async def search_hotels(
    city: str = Query(description="City name, e.g. Prague"),
    check_in: date = Query(description="Check-in date YYYY-MM-DD"),
    check_out: date = Query(description="Check-out date YYYY-MM-DD"),
    adults: int = Query(default=2, ge=1),
    children: int = Query(default=0, ge=0),
    country: str = Query(default="", description="Country name for more accurate results"),
    session=Depends(get_db),
):
    if not settings.SERPAPI_API_KEY and not settings.should_use_db_prices():
        raise HTTPException(status_code=503, detail="Hotel search is not configured (missing SERPAPI_API_KEY)")

    provider = get_accommodation_provider(session)
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
        return [_to_accommodation_summary(accommodation_to_dict(o)) for o in offers]
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
