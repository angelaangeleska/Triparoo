from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.recommendation.base import MemberContext, RecommendationContext
from app.recommendation.hybrid import HybridRecommendationService
from app.repositories.catalog import DestinationRepository
from app.schemas.family import TripMemberInput
from app.schemas.trip_planner import (
    AccommodationSummary,
    AttractionSummary,
    BookingSourceSummary,
    CheapestDatesRequest,
    CheapestDatesResponse,
    CheapestDestinationResult,
    CheapestDestinationsRequest,
    CheapestDestinationsResponse,
    CheapestPeriod,
    DestinationRecommendation,
    FlightSummary,
    RecommendRequest,
    RecommendResponse,
    ScoreBreakdown,
)
from app.services.cost_estimator import CostEstimatorService
from app.services.origin_resolver import OriginResolverService


class TripPlannerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dest_repo = DestinationRepository(session)
        self.cost_estimator = CostEstimatorService(session)
        self.origin_resolver = OriginResolverService(session)
        self.recommendation_service = HybridRecommendationService()

    async def _resolve_origin(self, request: RecommendRequest):
        resolved = None
        if request.origin_location:
            resolved = await self.origin_resolver.resolve(request.origin_location)
        origin_iatas, origin_airport_ids, origin_message = await self.origin_resolver.resolve_airports(
            request.origin_location, request.origin_airport_id
        )
        origin_airport_id = request.origin_airport_id
        if not origin_airport_id and resolved:
            origin_airport_id = resolved.primary_airport_id
        elif not origin_airport_id and origin_airport_ids:
            origin_airport_id = origin_airport_ids[0]
        origin_label = resolved.display_name if resolved else None
        return resolved, origin_iatas, origin_airport_ids, origin_airport_id, origin_message, origin_label

    def _to_context(
        self,
        request: RecommendRequest,
        origin_airport_id: int | None,
        origin_label: str | None,
    ) -> RecommendationContext:
        return RecommendationContext(
            members=[
                MemberContext(age=m.age, gender=m.gender, interests=m.interests)
                for m in request.members
            ],
            budget=request.budget,
            start_date=request.start_date,
            end_date=request.end_date,
            preferred_month=request.preferred_month or (request.start_date.month if request.start_date else None),
            origin_airport_id=origin_airport_id,
            origin_label=origin_label,
        )

    @staticmethod
    def _flight_summary(offer: dict | None) -> FlightSummary | None:
        if not offer:
            return None
        return FlightSummary(**offer)

    @staticmethod
    def _accommodation_summary(data: dict | None) -> AccommodationSummary | None:
        if not data:
            return None
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

    async def recommend(self, request: RecommendRequest) -> RecommendResponse:
        destinations = await self.dest_repo.list_with_relations()
        resolved, origin_iatas, origin_airport_ids, origin_airport_id, origin_message, origin_label = (
            await self._resolve_origin(request)
        )
        excluded = self.origin_resolver.get_excluded_destination_ids(
            destinations, origin_airport_ids, resolved, origin_iatas
        )
        eligible = [d for d in destinations if d.id not in excluded]
        context = self._to_context(request, origin_airport_id, origin_label)
        party_size = len(request.members)

        async def cost_fn(dest):
            return await self.cost_estimator.estimate_trip(
                dest,
                party_size,
                request.start_date,
                request.end_date,
                origin_location=request.origin_location,
                origin_airport_id=request.origin_airport_id,
            )

        ranked = await self.recommendation_service.rank(context, eligible, cost_fn)
        attr_map = {}
        for dest in destinations:
            for att in dest.attractions or []:
                attr_map[att.id] = att

        recommendations = []
        for r in ranked:
            attractions = [
                AttractionSummary(
                    id=attr_map[aid].id,
                    name=attr_map[aid].name,
                    category=attr_map[aid].category,
                    price=attr_map[aid].price,
                    min_age=attr_map[aid].min_age,
                    max_age=attr_map[aid].max_age,
                )
                for aid in r["suggested_attraction_ids"]
                if aid in attr_map
            ]
            recommendations.append(
                DestinationRecommendation(
                    destination_id=r["destination_id"],
                    city=r["city"],
                    country=r["country"],
                    rule_score=r["rule_score"],
                    llm_score=r["llm_score"],
                    final_score=r["final_score"],
                    estimated_total_cost=r["estimated_total_cost"],
                    flight_cost=r.get("flight_cost", 0.0),
                    accommodation_cost=r.get("accommodation_cost", 0.0),
                    activity_cost=r.get("activity_cost", 0.0),
                    flight=self._flight_summary(r.get("flight_offer")),
                    accommodation=self._accommodation_summary(r.get("accommodation_offer")),
                    score_breakdown=ScoreBreakdown(**r["score_breakdown"]),
                    explanation=r["explanation"],
                    suggested_attractions=attractions,
                )
            )
        return RecommendResponse(recommendations=recommendations, origin_message=origin_message)

    async def cheapest_destinations(self, request: CheapestDestinationsRequest) -> CheapestDestinationsResponse:
        destinations = await self.dest_repo.list_with_relations()
        resolved = None
        if request.origin_location:
            resolved = await self.origin_resolver.resolve(request.origin_location)
        origin_iatas, origin_airport_ids, _ = await self.origin_resolver.resolve_airports(
            request.origin_location, request.origin_airport_id
        )
        excluded = self.origin_resolver.get_excluded_destination_ids(
            destinations, origin_airport_ids, resolved, origin_iatas
        )
        results = []
        for dest in destinations:
            if dest.id in excluded:
                continue
            estimate = await self.cost_estimator.estimate_trip(
                dest,
                request.party_size,
                request.start_date,
                request.end_date,
                origin_location=request.origin_location,
                origin_airport_id=request.origin_airport_id,
            )
            if estimate.get("same_origin"):
                continue
            if estimate["total"] <= request.budget * 1.15:
                results.append(
                    CheapestDestinationResult(
                        destination_id=dest.id,
                        city=dest.city.name if dest.city else "",
                        country=dest.city.country.name if dest.city and dest.city.country else "",
                        estimated_total_cost=estimate["total"],
                        flight_cost=estimate["flight"],
                        accommodation_cost=estimate["accommodation"],
                        activity_cost=estimate["activity"],
                        nights=estimate["nights"],
                        flight=self._flight_summary(estimate.get("flight_offer")),
                    )
                )
        results.sort(key=lambda r: r.estimated_total_cost)
        return CheapestDestinationsResponse(results=results[:10])

    async def cheapest_dates(self, request: CheapestDatesRequest) -> CheapestDatesResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        periods = []
        for season in dest.seasons or []:
            mid_month = season.month_start
            today = date.today()
            year = today.year
            if mid_month < today.month or (mid_month == today.month and today.day > 10):
                year += 1
            sample_start = date(year, mid_month, 10)
            sample_end = sample_start + timedelta(days=5)
            estimate = await self.cost_estimator.estimate_trip(
                dest,
                request.party_size,
                sample_start,
                sample_end,
                origin_location=request.origin_location,
                origin_airport_id=request.origin_airport_id,
            )
            avg_acc = estimate["accommodation"] / max(estimate["nights"], 1)
            periods.append(
                CheapestPeriod(
                    season=season.season,
                    month_start=season.month_start,
                    month_end=season.month_end,
                    avg_flight_price=estimate["flight"],
                    avg_accommodation_price=round(avg_acc, 2),
                    estimated_total=estimate["total"],
                    weather_score=season.weather_score * 100,
                )
            )
        periods.sort(key=lambda p: p.estimated_total)
        return CheapestDatesResponse(
            destination_id=dest.id,
            city=dest.city.name if dest.city else "",
            country=dest.city.country.name if dest.city and dest.city.country else "",
            cheapest_periods=periods,
        )
