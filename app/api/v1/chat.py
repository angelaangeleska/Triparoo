from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repositories.catalog import DestinationRepository
from app.services.chat_service import chat_with_ai

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_async_session),
):
    dest_repo = DestinationRepository(session)
    destinations_db = await dest_repo.list_with_relations()
    
    destinations = [
        {
            "city": d.city.name if d.city else "",
            "country": d.city.country.name if d.city and d.city.country else "",
            "family_score": d.family_friendliness_score,
            "attractions": [a.name for a in (d.attractions or [])[:4]],
        }
        for d in destinations_db
    ]
    
    history = [{"role": m.role, "content": m.content} for m in request.history]
    
    response = await chat_with_ai(
        message=request.message,
        history=history,
        destinations=destinations,
    )
    
    return ChatResponse(response=response)