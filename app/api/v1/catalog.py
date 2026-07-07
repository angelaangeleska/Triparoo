from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import get_db
from app.models.accommodation import Accommodation
from app.models.activity import Activity
from app.models.attraction import Attraction
from app.models.country import Airport
from app.models.flight import Flight
from app.models.offer_cache import FlightOfferCache
from app.repositories.catalog import AirportRepository
from app.services.destination_catalog_service import DestinationCatalogService
from app.schemas.catalog import (
    AccommodationRead,
    ActivityRead,
    AirportRead,
    AirportSearchResult,
    AttractionRead,
    DestinationRead,
    FlightOfferCacheRead,
    FlightRead,
)
from app.services.airport_search import AirportSearchService

router = APIRouter(tags=["Catalog"])


@router.get("/airports", response_model=list[AirportRead])
async def list_airports(session=Depends(get_db)):
    repo = AirportRepository(session)
    airports = await repo.list_with_city()
    return [
        AirportRead(
            id=a.id,
            name=a.name,
            iata_code=a.iata_code,
            city_id=a.city_id,
            city_name=a.city.name if a.city else None,
        )
        for a in airports
    ]


@router.get("/airports/search", response_model=list[AirportSearchResult])
async def search_airports(
    q: str = Query(min_length=2, description="City, country, or IATA code"),
    limit: int = Query(default=20, ge=1, le=50),
    session=Depends(get_db),
):
    service = AirportSearchService(session)
    results = await service.search(q, limit=limit)
    return [
        AirportSearchResult(
            id=r.id,
            name=r.name,
            iata_code=r.iata_code,
            city_name=r.city_name,
            country_name=r.country_name,
            match_type=r.match_type,
            distance_km=r.distance_km,
            note=r.note,
        )
        for r in results
    ]


@router.get("/attractions", response_model=list[AttractionRead])
async def list_attractions(
    destination_id: int | None = Query(default=None),
    session=Depends(get_db),
):
    query = select(Attraction)
    if destination_id:
        query = query.where(Attraction.destination_id == destination_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/destinations", response_model=list[DestinationRead])
async def list_destinations(
    departure_iata: str = Query(default="SOF", min_length=3, max_length=3),
    adults: int = Query(default=2, ge=1, le=9),
    children: int = Query(default=0, ge=0, le=9),
    month: int = Query(default=0, ge=0, le=12),
    session=Depends(get_db),
):
    service = DestinationCatalogService(session)
    return await service.list_destinations(
        departure_iata=departure_iata.upper(),
        adults=adults,
        children=children,
        month=month,
    )


@router.get("/destinations/{destination_id}", response_model=DestinationRead)
async def get_destination(destination_id: int, session=Depends(get_db)):
    from fastapi import HTTPException

    service = DestinationCatalogService(session)
    dest = await service.get_destination(destination_id)
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    return dest


@router.get("/activities", response_model=list[ActivityRead])
async def list_activities(
    destination_id: int | None = Query(default=None),
    session=Depends(get_db),
):
    query = select(Activity)
    if destination_id:
        query = query.where(Activity.destination_id == destination_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/accommodations", response_model=list[AccommodationRead])
async def list_accommodations(
    destination_id: int | None = Query(default=None),
    session=Depends(get_db),
):
    query = select(Accommodation)
    if destination_id:
        query = query.where(Accommodation.destination_id == destination_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/flight-offers", response_model=list[FlightOfferCacheRead])
async def list_flight_offers(
    origin_iata: str | None = Query(default=None, min_length=3, max_length=3),
    destination_iata: str | None = Query(default=None, min_length=3, max_length=3),
    session=Depends(get_db),
):
    """Cached flight offers (SerpAPI-shaped test data stored in flight_offer_cache)."""
    query = select(FlightOfferCache).order_by(FlightOfferCache.id)
    if origin_iata:
        query = query.where(FlightOfferCache.origin_iata == origin_iata.upper())
    if destination_iata:
        query = query.where(FlightOfferCache.destination_iata == destination_iata.upper())
    result = await session.execute(query)
    rows = result.scalars().all()
    return [
        FlightOfferCacheRead(
            id=row.id,
            origin_iata=row.origin_iata,
            destination_iata=row.destination_iata,
            departure_date=row.departure_date.isoformat(),
            return_date=row.return_date.isoformat() if row.return_date else None,
            party_size=row.party_size,
            total_price=float(row.payload.get("total_price") or 0),
            airline=(row.payload.get("outbound") or {}).get("airline", ""),
            source=row.payload.get("source", "db"),
        )
        for row in rows
    ]


async def _flights_from_cache(
    session,
    origin: int | None,
    destination: int | None,
) -> list[FlightRead]:
    airport_result = await session.execute(select(Airport))
    airports = {a.iata_code.upper(): a for a in airport_result.scalars().all()}

    cache_result = await session.execute(select(FlightOfferCache).order_by(FlightOfferCache.id))
    rows = cache_result.scalars().all()
    flights: list[FlightRead] = []

    for row in rows:
        origin_ap = airports.get(row.origin_iata.upper())
        dest_ap = airports.get(row.destination_iata.upper())
        if not origin_ap or not dest_ap:
            continue
        if origin and origin_ap.id != origin:
            continue
        if destination and dest_ap.id != destination:
            continue
        outbound = row.payload.get("outbound") or {}
        dep_raw = outbound.get("departure_date") or f"{row.departure_date.isoformat()}T10:00:00"
        flights.append(
            FlightRead(
                id=row.id,
                origin_airport_id=origin_ap.id,
                destination_airport_id=dest_ap.id,
                departure_date=dep_raw,
                price=float(row.payload.get("total_price") or outbound.get("price") or 0),
                airline=outbound.get("airline", "Unknown"),
                seats_remaining=outbound.get("seats_remaining"),
            )
        )
    return flights


@router.get("/flights", response_model=list[FlightRead])
async def list_flights(
    origin: int | None = Query(default=None),
    destination: int | None = Query(default=None),
    session=Depends(get_db),
):
    query = select(Flight)
    if origin:
        query = query.where(Flight.origin_airport_id == origin)
    if destination:
        query = query.where(Flight.destination_airport_id == destination)
    result = await session.execute(query)
    flights = result.scalars().all()
    if flights:
        return [
            FlightRead(
                id=f.id,
                origin_airport_id=f.origin_airport_id,
                destination_airport_id=f.destination_airport_id,
                departure_date=f.departure_date.isoformat(),
                price=f.price,
                airline=f.airline,
                seats_remaining=f.seats_remaining,
            )
            for f in flights
        ]
    return await _flights_from_cache(session, origin, destination)
