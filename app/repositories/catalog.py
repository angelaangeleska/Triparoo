from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.country import Airport, City, Country
from app.models.destination import Destination
from app.models.user import User
from app.repositories.base import GenericRepository


class UserRepository(GenericRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


class DestinationRepository(GenericRepository[Destination]):
    model = Destination

    async def list_with_relations(self) -> list[Destination]:
        result = await self.session.execute(
            select(Destination)
            .options(
                selectinload(Destination.city).selectinload(City.country),
                selectinload(Destination.city).selectinload(City.airports),
                selectinload(Destination.seasons),
                selectinload(Destination.attractions),
                selectinload(Destination.accommodations),
            )
        )
        return list(result.scalars().unique().all())

    async def get_with_relations(self, destination_id: int) -> Destination | None:
        result = await self.session.execute(
            select(Destination)
            .where(Destination.id == destination_id)
            .options(
                selectinload(Destination.city).selectinload(City.country),
                selectinload(Destination.city).selectinload(City.airports),
                selectinload(Destination.seasons),
                selectinload(Destination.attractions),
                selectinload(Destination.accommodations),
            )
        )
        return result.scalar_one_or_none()


class AirportRepository(GenericRepository[Airport]):
    model = Airport

    async def get_by_iata(self, iata_code: str) -> Airport | None:
        result = await self.session.execute(select(Airport).where(Airport.iata_code == iata_code))
        return result.scalar_one_or_none()

    async def list_with_city(self) -> list[Airport]:
        result = await self.session.execute(select(Airport).options(selectinload(Airport.city)))
        return list(result.scalars().all())
