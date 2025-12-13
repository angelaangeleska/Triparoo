from typing import Literal, Optional

from pydantic import BaseModel

AccommodationType = Literal["hotel", "motel", "resort", "hostel", "bnb", "apartment"]

class Accommodation(BaseModel):
    id: int
    destination_id: int
    type: AccommodationType
    rating: Optional[float] = None
    price_per_night: Optional[float] = None
    address: Optional[str] = None