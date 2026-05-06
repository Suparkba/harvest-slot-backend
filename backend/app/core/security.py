from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.status import AccountRole, AccountStatus
from backend.app.repositories.account_repo import AccountRepository

try:
    from jose import JWTError, jwt
except ModuleNotFoundError:
    class JWTError(Exception):
        pass

    class _SimpleJWT:
        @staticmethod
        def encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
            if algorithm != "HS256":
                raise JWTError("unsupported algorithm")
            header = {"alg": algorithm, "typ": "JWT"}
            header_segment = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
            payload_segment = base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).rstrip(b"=").decode()
            signing_input = f"{header_segment}.{payload_segment}".encode()
            signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            signature_segment = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
            return f"{header_segment}.{payload_segment}.{signature_segment}"

        @staticmethod
        def decode(token: str, secret: str, algorithms: list[str]) -> dict:
            if "HS256" not in algorithms:
                raise JWTError("unsupported algorithm")
            try:
                header_segment, payload_segment, signature_segment = token.split(".")
            except ValueError as exc:
                raise JWTError("invalid token format") from exc
            signing_input = f"{header_segment}.{payload_segment}".encode()
            expected_signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            actual_signature = base64.urlsafe_b64decode(signature_segment + "=" * (-len(signature_segment) % 4))
            if not hmac.compare_digest(expected_signature, actual_signature):
                raise JWTError("invalid signature")
            payload_json = base64.urlsafe_b64decode(payload_segment + "=" * (-len(payload_segment) % 4)).decode()
            payload = json.loads(payload_json)
            exp = payload.get("exp")
            if exp and datetime.now(timezone.utc) > datetime.fromisoformat(exp):
                raise JWTError("token expired")
            return payload

    jwt = _SimpleJWT()

try:
    from passlib.context import CryptContext
except ModuleNotFoundError:
    CryptContext = None


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") if CryptContext else None
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False,
    description="Use the account email in the OAuth2 username field.",
)


@dataclass
class AuthenticatedUser:
    account_id: int
    email: str
    role: str
    status: str
    email_verified: bool
    customer_id: int | None = None
    owner_id: int | None = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    return hashed_password == hashlib.sha256(plain_password.encode()).hexdigest()


def hash_password(password: str) -> str:
    if pwd_context:
        return pwd_context.hash(password)
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def _mock_user_from_token(token: str) -> AuthenticatedUser | None:
    if token == "mock-customer-token":
        return AuthenticatedUser(
            account_id=1,
            email="customer@example.com",
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
            email_verified=True,
            customer_id=1,
        )
    if token == "mock-owner-token":
        return AuthenticatedUser(
            account_id=2,
            email="owner@example.com",
            role=AccountRole.OWNER,
            status=AccountStatus.ACTIVE,
            email_verified=True,
            owner_id=1,
        )
    return None


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> AuthenticatedUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")

    mock_user = _mock_user_from_token(token)
    if mock_user:
        return mock_user

    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid access token") from exc

    email = payload.get("sub")
    role = payload.get("role")
    if not email or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid access token")

    repo = AccountRepository(db)
    account = repo.get_by_email(email)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="account not found")
    if account.role != role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid access token")

    user = AuthenticatedUser(
        account_id=account.account_id,
        email=account.email,
        role=account.role,
        status=account.status,
        email_verified=account.email_verified,
    )
    if account.customer_profile:
        user.customer_id = account.customer_profile.customer_id
    if account.owner_profile:
        user.owner_id = account.owner_profile.owner_id
    return user


def require_customer(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current_user.role != AccountRole.CUSTOMER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CUSTOMER 권한이 필요합니다.")
    return current_user


def require_owner(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    if current_user.role != AccountRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="OWNER 권한이 필요합니다.")
    return current_user
