from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    passport_number: Optional[str] = None