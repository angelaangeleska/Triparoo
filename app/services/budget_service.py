from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.catalog import DestinationRepository
from app.schemas.trip_planner import BudgetAlternative, BudgetOptimizeRequest, BudgetOptimizeResponse
from app.services.cost_estimator import CostEstimatorService


class BudgetOptimizationService:
    def __init__(self, session: AsyncSession):
        self.dest_repo = DestinationRepository(session)
        self.cost_estimator = CostEstimatorService(session)

    async def optimize(self, request: BudgetOptimizeRequest) -> BudgetOptimizeResponse:
        dest = await self.dest_repo.get_with_relations(request.destination_id)
        if not dest:
            raise NotFoundError("Destination not found")

        current = await self.cost_estimator.estimate_trip(
            dest,
            len(request.members),
            request.start_date,
            request.end_date,
            origin_location=request.origin_location,
            origin_airport_id=request.origin_airport_id,
        )
        alternatives = []

        if current["total"] > request.budget:
            cheaper_date_start = request.start_date - timedelta(days=14)
            cheaper_end = request.end_date - timedelta(days=14)
            alt_estimate = await self.cost_estimator.estimate_trip(
                dest,
                len(request.members),
                cheaper_date_start,
                cheaper_end,
                origin_location=request.origin_location,
                origin_airport_id=request.origin_airport_id,
            )
            if alt_estimate["total"] < current["total"]:
                alternatives.append(
                    BudgetAlternative(
                        type="cheaper_dates",
                        description="Travel two weeks earlier for lower seasonal prices",
                        estimated_savings=round(current["total"] - alt_estimate["total"], 2),
                        new_total=alt_estimate["total"],
                    )
                )

            if dest.accommodations:
                cheapest = min(dest.accommodations, key=lambda a: a.price_per_night)
                nights = current["nights"]
                savings = current["accommodation"] - cheapest.price_per_night * nights
                if savings > 0:
                    alternatives.append(
                        BudgetAlternative(
                            type="cheaper_accommodation",
                            description=f"Switch to {cheapest.name} ({cheapest.type})",
                            estimated_savings=round(savings, 2),
                            new_total=round(current["total"] - savings, 2),
                        )
                    )

            all_dests = await self.dest_repo.list_with_relations()
            for alt_dest in all_dests:
                if alt_dest.id == dest.id:
                    continue
                alt_cost = await self.cost_estimator.estimate_trip(
                    alt_dest,
                    len(request.members),
                    request.start_date,
                    request.end_date,
                    origin_location=request.origin_location,
                    origin_airport_id=request.origin_airport_id,
                )
                if alt_cost["total"] < current["total"] and alt_cost["total"] <= request.budget:
                    alternatives.append(
                        BudgetAlternative(
                            type="alternative_destination",
                            description=f"Consider {alt_dest.city.name} instead",
                            estimated_savings=round(current["total"] - alt_cost["total"], 2),
                            new_total=alt_cost["total"],
                        )
                    )
                    break

        return BudgetOptimizeResponse(
            current_estimate=current["total"],
            budget=request.budget,
            within_budget=current["total"] <= request.budget,
            alternatives=alternatives,
        )
