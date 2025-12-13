from typing import Optional

from pydantic import BaseModel


class Activity(BaseModel):
    id: int
    destination_id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None