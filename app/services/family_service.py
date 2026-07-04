"""CRUD for a user's saved family members.

Persisted per-user so the Trip Planner and the Kids Activities tab share one
family profile instead of asking for children's ages/interests twice.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.family_member import FamilyMember
from app.repositories.family import FamilyMemberRepository
from app.schemas.family import FamilyMemberCreate


class FamilyMemberService:
    def __init__(self, session: AsyncSession):
        self.repo = FamilyMemberRepository(session)

    async def list_for_user(self, user_id: int) -> list[FamilyMember]:
        return await self.repo.list_for_user(user_id)

    async def create(self, user_id: int, data: FamilyMemberCreate) -> FamilyMember:
        member = FamilyMember(user_id=user_id, **data.model_dump())
        return await self.repo.create(member)

    async def update(self, user_id: int, member_id: int, data: FamilyMemberCreate) -> FamilyMember:
        member = await self._get_owned(user_id, member_id)
        for field, value in data.model_dump().items():
            setattr(member, field, value)
        await self.repo.session.flush()
        return member

    async def delete(self, user_id: int, member_id: int) -> None:
        member = await self._get_owned(user_id, member_id)
        await self.repo.delete(member)

    async def _get_owned(self, user_id: int, member_id: int) -> FamilyMember:
        member = await self.repo.get_by_id(member_id)
        # 404 (not 403) on a member owned by someone else, to avoid leaking existence.
        if not member or member.user_id != user_id:
            raise NotFoundError("Family member not found")
        return member
