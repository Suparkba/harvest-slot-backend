from json import JSONDecodeError

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import AuthenticatedUser, get_current_user
from backend.app.schemas.auth_schema import (
    EmailResendRequest,
    EmailVerificationSendRequest,
    EmailVerifyRequest,
    LoginRequest,
    SignupRequest,
)
from backend.app.schemas.common_schema import success_response
from backend.app.services.auth_service import AuthService
from backend.app.services.email_verification_service import EmailVerificationService


router = APIRouter()
FORM_CONTENT_TYPES = {"application/x-www-form-urlencoded", "multipart/form-data"}


async def parse_login_request(request: Request) -> LoginRequest:
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()

    try:
        if content_type in FORM_CONTENT_TYPES:
            form_data = await request.form()
            raw_payload = {
                "email": form_data.get("username"),
                "password": form_data.get("password"),
            }
        else:
            raw_payload = await request.json()
    except JSONDecodeError as exc:
        raise RequestValidationError(
            [{"type": "json_invalid", "loc": ("body",), "msg": "JSON decode error", "input": None}]
        ) from exc

    try:
        return LoginRequest.model_validate(raw_payload)
    except ValidationError as exc:
        errors = []
        for error in exc.errors():
            loc = tuple(error.get("loc", ()))
            if content_type in FORM_CONTENT_TYPES and loc == ("email",):
                loc = ("body", "username")
            else:
                loc = ("body", *loc)
            errors.append({**error, "loc": loc})
        raise RequestValidationError(errors) from exc


@router.post("/auth/customers/signup")
def customer_signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict:
    return success_response(AuthService(db).signup_customer(**payload.model_dump()))


@router.post("/auth/owners/signup")
def owner_signup(payload: SignupRequest, db: Session = Depends(get_db)) -> dict:
    return success_response(AuthService(db).signup_owner(**payload.model_dump()))


@router.post("/auth/email/resend")
def resend_email(payload: EmailResendRequest, db: Session = Depends(get_db)) -> dict:
    data = EmailVerificationService(db).send_verification(**payload.model_dump())
    return success_response(data, message="verification email sent")


@router.post("/auth/email/send")
def send_email_verification(payload: EmailVerificationSendRequest, db: Session = Depends(get_db)) -> dict:
    data = EmailVerificationService(db).send_verification(**payload.model_dump())
    return success_response(data, message="verification email sent")


@router.post("/auth/email/verify")
def verify_email(payload: EmailVerifyRequest, db: Session = Depends(get_db)) -> dict:
    data = EmailVerificationService(db).verify_code(
        email=payload.email,
        code=payload.code or "",
        purpose=payload.purpose,
    )
    return success_response(data, message="email verified")


@router.get("/auth/email/status")
def email_verification_status(email: str, purpose: str = "SIGNUP", db: Session = Depends(get_db)) -> dict:
    return success_response(EmailVerificationService(db).get_status(email=email, purpose=purpose))


@router.post(
    "/auth/login",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "title": "LoginRequest",
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "email": {"type": "string", "title": "Email"},
                            "password": {"type": "string", "title": "Password"},
                        },
                    },
                    "example": {
                        "email": "owner@test.com",
                        "password": "demo1234!",
                    },
                }
            },
        }
    },
)
async def login(payload: LoginRequest = Depends(parse_login_request), db: Session = Depends(get_db)) -> dict:
    return success_response(AuthService(db).login(**payload.model_dump()))


@router.post("/auth/token")
def issue_oauth2_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    token_data = AuthService(db).login(email=form_data.username, password=form_data.password)
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"],
    }


@router.get("/me")
def me(current_user: AuthenticatedUser = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return success_response(AuthService(db).get_me(current_user.account_id))
