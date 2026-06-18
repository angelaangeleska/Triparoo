import logging
import re
from datetime import date
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, get_db, handle_app_exception
from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError
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

_SERPAPI_URL = "https://serpapi.com/search"
_FAMILY_KEYWORDS = {"pool", "kids", "family", "children", "playground", "babysit", "crib"}


def _price(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_hotel(prop: dict, nights: int) -> AccommodationSummary | None:
    name = prop.get("name", "").strip()
    if not name:
        return None

    rate_block = prop.get("rate_per_night") or {}
    total_block = prop.get("total_rate") or {}

    price_per_night = _price(rate_block.get("extracted_lowest")) or _price(rate_block.get("lowest"))
    total_price = (
        _price(total_block.get("extracted_lowest"))
        or _price(total_block.get("lowest"))
        or round(price_per_night * nights, 2)
    )
    if price_per_night == 0:
        return None

    amenities: list[str] = prop.get("amenities") or []
    family_friendly = any(k in " ".join(amenities).lower() for k in _FAMILY_KEYWORDS)

    booking_sources: list[BookingSourceSummary] = []
    for p in (prop.get("prices") or [])[:5]:
        link = p.get("link", "")
        if not link:
            continue
        sp = _price(p.get("extracted_rate_per_night")) or _price(p.get("rate_per_night")) or price_per_night
        st = _price(p.get("extracted_total_rate")) or _price(p.get("total_rate")) or total_price
        booking_sources.append(BookingSourceSummary(
            name=p.get("source", "Book"),
            price_per_night=round(sp, 2),
            total_price=round(st, 2),
            currency="USD",
            url=link,
        ))

    images = prop.get("images") or []
    image_url = images[0].get("thumbnail", "") if images else ""
    rating_raw = prop.get("overall_rating")

    return AccommodationSummary(
        name=name,
        type=prop.get("type", "Hotel"),
        hotel_class=prop.get("hotel_class", ""),
        rating=float(rating_raw) if rating_raw else None,
        reviews_count=prop.get("reviews"),
        price_per_night=round(price_per_night, 2),
        total_price=round(total_price, 2),
        currency="USD",
        family_friendly=family_friendly,
        image_url=image_url,
        google_url=prop.get("link", ""),
        booking_sources=booking_sources,
        amenities=amenities[:10],
        check_in_time=prop.get("check_in_time", ""),
        check_out_time=prop.get("check_out_time", ""),
        source="serpapi",
    )


@router.get("/hotels", response_model=list[AccommodationSummary])
async def search_hotels(
    city: str = Query(description="City name, e.g. Prague"),
    check_in: date = Query(description="Check-in date YYYY-MM-DD"),
    check_out: date = Query(description="Check-out date YYYY-MM-DD"),
    adults: int = Query(default=2, ge=1),
    children: int = Query(default=0, ge=0),
):
    if not settings.SERPAPI_API_KEY:
        raise HTTPException(status_code=503, detail="Hotel search is not configured (missing SERPAPI_API_KEY)")

    nights = max((check_out - check_in).days, 1)
    params: dict = {
        "engine": "google_hotels",
        "q": city,
        "check_in_date": check_in.isoformat(),
        "check_out_date": check_out.isoformat(),
        "adults": adults,
        "currency": "USD",
        "sort_by": "3",
        "hl": "en",
        "api_key": settings.SERPAPI_API_KEY,
    }
    if children > 0:
        params["children"] = children

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_SERPAPI_URL, params=params)

        data = resp.json()
        if resp.status_code == 429 or "run out of searches" in data.get("error", ""):
            raise HTTPException(status_code=503, detail="SerpAPI quota exhausted — please top up at serpapi.com/manage-api-key")
        if "error" in data:
            raise HTTPException(status_code=502, detail=f"Hotel search error: {data['error']}")
        if resp.status_code != 200:
            logger.error("SerpAPI hotels %s: %s", resp.status_code, resp.text[:300])
            raise HTTPException(status_code=502, detail=f"Hotel search failed (SerpAPI {resp.status_code})")

        properties = data.get("properties") or []
        hotels = [h for p in properties[:20] if (h := _parse_hotel(p, nights)) is not None]
        return sorted(hotels, key=lambda h: h.price_per_night)[:12]

    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Hotel search timed out")
    except Exception as exc:
        logger.exception("Hotel search failed")
        raise HTTPException(status_code=500, detail=str(exc))


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
