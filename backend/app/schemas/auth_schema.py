from pydantic import BaseModel, ConfigDict, Field, model_validator


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    name: str
    phone: str


class EmailResendRequest(BaseModel):
    email: str = Field(json_schema_extra={"example": "customer@example.com"})
    purpose: str = Field(default="SIGNUP", json_schema_extra={"example": "SIGNUP"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "purpose": "SIGNUP",
            }
        }
    )


class EmailVerificationSendRequest(BaseModel):
    email: str = Field(json_schema_extra={"example": "customer@example.com"})
    purpose: str = Field(default="SIGNUP", json_schema_extra={"example": "SIGNUP"})

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "purpose": "SIGNUP",
            }
        }
    )


class EmailVerifyRequest(BaseModel):
    email: str = Field(json_schema_extra={"example": "customer@example.com"})
    code: str | None = Field(default=None, json_schema_extra={"example": "123456"})
    purpose: str = Field(default="SIGNUP", json_schema_extra={"example": "SIGNUP"})
    verification_code: str | None = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def fill_code_from_legacy_field(cls, values: dict):
        if isinstance(values, dict) and not values.get("code") and values.get("verification_code"):
            values["code"] = values["verification_code"]
        return values

    @model_validator(mode="after")
    def ensure_code_present(self):
        if not self.code:
            raise ValueError("code is required")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "code": "123456",
                "purpose": "SIGNUP",
            }
        }
    )


class EmailVerificationStatusRequest(BaseModel):
    email: str = Field(json_schema_extra={"example": "customer@example.com"})
    purpose: str = Field(default="SIGNUP", json_schema_extra={"example": "SIGNUP"})


class EmailVerificationResponse(BaseModel):
    email: str
    purpose: str
    verified: bool | None = None
    expires_in_minutes: int | None = None
    resend_available_seconds: int | None = None
    dev_code: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "customer@example.com",
                "purpose": "SIGNUP",
                "verified": True,
            }
        }
    )


class LoginRequest(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "owner@test.com",
                "password": "demo1234!",
            }
        }
    )


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
