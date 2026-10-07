from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Số giây token còn hiệu lực")
    user: UserRead
