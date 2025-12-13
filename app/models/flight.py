from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Flight(BaseModel):
    id: int
    origin_airport_id: int
    destination_airport_id: int
    departure_date: datetime
    price: float
    airline: str
    seats_remaining: Optional[int] = None