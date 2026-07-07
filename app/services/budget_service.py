from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.integrations.accommodations.base import AccommodationSearchCriteria
from app.integrations.accommodations.factory import get_accommodation_provider
from app.repositories.catalog import DestinationRepository
from app.schemas.trip_planner import (
    BudgetAlternative,
    BudgetOptimizeRequest,
    BudgetOptimizeResponse,
)
from app.services.accommodation_selection import offer_to_summary, same_accommodation, summary_total
from app.services.cost_estimator import CostEstimatorService


class BudgetOptimizationService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)
        self.cost_estimator = CostEstimatorService(session)
        self.accommodation_provider = get_accommodation_provider(session)

    async def optimize(self, request: BudgetOptimizeRequest) -> BudgetOptimizeResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        party_size = len(request.members)
        baseline = await self.cost_estimator.estimate_trip(
            dest,
            party_size,
            request.start_date,
            request.end_date,
            origin_location=request.origin_location,
            origin_airport_id=request.origin_airport_id,
        )

        flight_cost = baseline["flight"]
        activity_cost = baseline["activity"]
        nights = baseline["nights"]
        selected = request.selected_accommodation
        accommodation_cost = summary_total(selected) if selected else baseline["accommodation"]
        total = round(flight_cost + activity_cost + accommodation_cost, 2)
        within_budget = total <= request.budget
        alternatives: list[BudgetAlternative] = []

        if total > request.budget:
            alternatives.extend(
                await self._hotel_alternatives(
                    dest,
                    request,
                    party_size,
                    flight_cost,
                    activity_cost,
                    total,
                    selected,
                )
            )
            alternatives.extend(
                await self._non_hotel_alternatives(
                    dest,
                    request,
                    party_size,
                    baseline["total"],
                )
            )

        return BudgetOptimizeResponse(
            current_estimate=total,
            budget=request.budget,
            within_budget=within_budget,
            flight_cost=round(flight_cost, 2),
            accommodation_cost=round(accommodation_cost, 2),
            activity_cost=round(activity_cost, 2),
            nights=nights,
            selected_accommodation=selected,
            alternatives=alternatives[:5],
        )

    async def _hotel_alternatives(
        self,
        dest,
        request: BudgetOptimizeRequest,
        party_size: int,
        flight_cost: float,
        activity_cost: float,
        current_total: float,
        selected,
    ) -> list[BudgetAlternative]:
        city_name = dest.city.name if dest.city else ""
        country_name = dest.city.country.name if dest.city and dest.city.country else ""
        if not city_name:
            return []

        hotels = await self.accommodation_provider.search(
            AccommodationSearchCriteria(
                city=city_name,
                check_in=request.start_date,
                check_out=request.end_date,
                adults=party_size,
                country=country_name,
            )
        )
        if not hotels:
            return []

        results: list[BudgetAlternative] = []
        seen_names: set[str] = set()

        for offer in hotels:
            summary = offer_to_summary(offer)
            if same_accommodation(summary, selected):
                continue
            key = summary.name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            new_total = round(flight_cost + activity_cost + summary.total_price, 2)
            if new_total > request.budget:
                continue

            savings = round(current_total - new_total, 2)
            if savings <= 0:
                continue

            results.append(
                BudgetAlternative(
                    type="cheaper_accommodation",
                    description=f"{summary.name} keeps you within budget",
                    estimated_savings=savings,
                    new_total=new_total,
                    accommodation=summary,
                )
            )

        if results:
            return sorted(results, key=lambda a: a.new_total)[:3]

        for offer in hotels:
            summary = offer_to_summary(offer)
            if same_accommodation(summary, selected):
                continue
            key = summary.name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            new_total = round(flight_cost + activity_cost + summary.total_price, 2)
            if new_total >= current_total:
                continue

            results.append(
                BudgetAlternative(
                    type="cheaper_accommodation",
                    description=f"Save with {summary.name}",
                    estimated_savings=round(current_total - new_total, 2),
                    new_total=new_total,
                    accommodation=summary,
                )
            )
            if len(results) >= 3:
                break

        return results

    async def _non_hotel_alternatives(
        self,
        dest,
        request: BudgetOptimizeRequest,
        party_size: int,
        baseline_total: float,
    ) -> list[BudgetAlternative]:
        from datetime import timedelta

        alternatives: list[BudgetAlternative] = []

        cheaper_date_start = request.start_date - timedelta(days=14)
        cheaper_end = request.end_date - timedelta(days=14)
        alt_estimate = await self.cost_estimator.estimate_trip(
            dest,
            party_size,
            cheaper_date_start,
            cheaper_end,
            origin_location=request.origin_location,
            origin_airport_id=request.origin_airport_id,
        )
        if alt_estimate["total"] < baseline_total:
            alternatives.append(
                BudgetAlternative(
                    type="cheaper_dates",
                    description="Travel two weeks earlier for lower seasonal prices",
                    estimated_savings=round(baseline_total - alt_estimate["total"], 2),
                    new_total=alt_estimate["total"],
                )
            )

        all_dests = await self.dest_repo.list_with_relations()
        for alt_dest in all_dests:
            if alt_dest.id == dest.id:
                continue
            alt_cost = await self.cost_estimator.estimate_trip(
                alt_dest,
                party_size,
                request.start_date,
                request.end_date,
                origin_location=request.origin_location,
                origin_airport_id=request.origin_airport_id,
            )
            if alt_cost["total"] < baseline_total and alt_cost["total"] <= request.budget:
                alternatives.append(
                    BudgetAlternative(
                        type="alternative_destination",
                        description=f"Consider {alt_dest.city.name} instead",
                        estimated_savings=round(baseline_total - alt_cost["total"], 2),
                        new_total=alt_cost["total"],
                    )
                )
                break

        return alternatives
