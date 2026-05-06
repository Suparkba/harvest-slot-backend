from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str
    phone: str


class EmailResendRequest(BaseModel):
    email: str
    purpose: str = "SIGNUP"


class EmailVerifyRequest(BaseModel):
    email: str
    verification_code: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class MeResponse(BaseModel):
    account_id: int
    email: str
    role: str
    status: str
    email_verified: bool
    customer_profile: dict | None = None
    owner_profile: dict | None = None

    model_config = ConfigDict(from_attributes=True)
