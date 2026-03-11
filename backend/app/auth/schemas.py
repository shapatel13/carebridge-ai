from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    hospital_id: str
    hospital_name: str | None = None
    is_demo: bool = False

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    refresh_token: str
