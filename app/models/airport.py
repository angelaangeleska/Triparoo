from pydantic import BaseModel


class Airport(BaseModel):
    id: int
    name: str
    city_id: int
    country_id: int