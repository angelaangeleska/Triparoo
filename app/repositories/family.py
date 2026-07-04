from sqlalchemy import select

from app.models.family_member import FamilyMember
from app.repositories.base import GenericRepository


class FamilyMemberRepository(GenericRepository[FamilyMember]):
    model = FamilyMember

    async def list_for_user(self, user_id: int) -> list[FamilyMember]:
        result = await self.session.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id).order_by(FamilyMember.id)
        )
        return list(result.scalars().all())
