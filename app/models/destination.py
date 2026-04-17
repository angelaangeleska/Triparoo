from typing import Optional

from pydantic import BaseModel


class Destination(BaseModel):
    id: int
    city: str
    country: str
    airport_id: Optional[int] = None
    