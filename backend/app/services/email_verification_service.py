from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import hmac
import logging
import re
from secrets import randbelow

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.account import Account, EmailVerification
from backend.app.services.email_service import EmailDeliveryError, EmailService


logger = logging.getLogger(__name__)
EMAIL_REGEX = re.compile(r"^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$", re.IGNORECASE)


def normalize_email(email: str) -> str:
    return email.strip().lower()


class EmailVerificationService:
    def __init__(self, session: Session, email_service: EmailService | None = None):
        self.session = session
        self.email_service = email_service or EmailService()

    @staticmethod
    def validate_email_format(email: str) -> None:
        if not EMAIL_REGEX.match(email):
            raise HTTPException(status_code=400, detail="invalid email format")

    @staticmethod
    def generate_code() -> str:
        return f"{randbelow(1000000):06d}"

    @staticmethod
    def hash_code(email: str, purpose: str, code: str) -> str:
        payload = f"{email}:{purpose}:{code}".encode()
        return hmac.new(settings.jwt_secret_key.encode(), payload, hashlib.sha256).hexdigest()

    def _latest_verification(self, email: str, purpose: str) -> EmailVerification | None:
        return (
            self.session.query(EmailVerification)
            .filter(EmailVerification.email == email, EmailVerification.purpose == purpose)
            .order_by(EmailVerification.created_at.desc(), EmailVerification.email_verification_id.desc())
            .first()
        )

    def _mark_previous_codes_expired(self, email: str, purpose: str) -> None:
        previous_rows = (
            self.session.query(EmailVerification)
            .filter(
                EmailVerification.email == email,
                EmailVerification.purpose == purpose,
                EmailVerification.verified.is_(False),
                EmailVerification.expires_at > datetime.utcnow(),
            )
            .all()
        )
        for row in previous_rows:
            row.expires_at = datetime.utcnow()

    def _get_account(self, email: str) -> Account | None:
        return self.session.query(Account).filter(Account.email == email).first()

    def send_verification(self, email: str, purpose: str = "SIGNUP") -> dict:
        normalized_email = normalize_email(email)
        self.validate_email_format(normalized_email)
        purpose = purpose.strip().upper()

        latest = self._latest_verification(normalized_email, purpose)
        cooldown = settings.email_verification_resend_cooldown_seconds
        if latest and (datetime.utcnow() - latest.created_at).total_seconds() < cooldown:
            raise HTTPException(status_code=429, detail="verification resend cooldown")

        code = self.generate_code()
        code_hash = self.hash_code(normalized_email, purpose, code)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.email_verification_expire_minutes)
        self._mark_previous_codes_expired(normalized_email, purpose)

        account = self._get_account(normalized_email)
        verification = EmailVerification(
            account_id=account.account_id if account else None,
            email=normalized_email,
            purpose=purpose,
            code_hash=code_hash,
            verified=False,
            expires_at=expires_at,
            verified_at=None,
            attempt_count=0,
        )
        self.session.add(verification)
        self.session.flush()

        try:
            self.email_service.send_verification_email(
                normalized_email,
                code,
                settings.email_verification_expire_minutes,
            )
        except EmailDeliveryError:
            self.session.rollback()
            raise HTTPException(status_code=500, detail="failed to send verification email")

        self.session.commit()
        response = {
            "email": normalized_email,
            "purpose": purpose,
            "expires_in_minutes": settings.email_verification_expire_minutes,
            "resend_available_seconds": settings.email_verification_resend_cooldown_seconds,
        }
        if settings.email_dev_mode:
            response["dev_code"] = code
        return response

    def verify_code(self, email: str, code: str, purpose: str = "SIGNUP") -> dict:
        normalized_email = normalize_email(email)
        self.validate_email_format(normalized_email)
        purpose = purpose.strip().upper()

        verification = self._latest_verification(normalized_email, purpose)
        if not verification:
            raise HTTPException(status_code=400, detail="verification request not found")
        if verification.verified:
            raise HTTPException(status_code=400, detail="verification code already used")
        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="verification code expired")
        if verification.attempt_count >= settings.email_verification_max_attempts:
            raise HTTPException(status_code=429, detail="verification attempts exceeded")

        if verification.code_hash != self.hash_code(normalized_email, purpose, code):
            verification.attempt_count += 1
            self.session.commit()
            if verification.attempt_count >= settings.email_verification_max_attempts:
                raise HTTPException(status_code=429, detail="verification attempts exceeded")
            raise HTTPException(status_code=400, detail="invalid verification code")

        verification.verified = True
        verification.verified_at = datetime.utcnow()
        account = self._get_account(normalized_email)
        if account:
            account.email_verified = True
            verification.account_id = account.account_id
        self.session.commit()
        return {
            "email": normalized_email,
            "purpose": purpose,
            "verified": True,
        }

    def get_status(self, email: str, purpose: str = "SIGNUP") -> dict:
        normalized_email = normalize_email(email)
        self.validate_email_format(normalized_email)
        purpose = purpose.strip().upper()
        verification = self._latest_verification(normalized_email, purpose)
        verified = bool(verification and verification.verified and verification.verified_at)
        return {
            "email": normalized_email,
            "purpose": purpose,
            "verified": verified,
        }

    def ensure_verified_for_signup(self, email: str) -> None:
        if not settings.email_verification_required:
            return
        status = self.get_status(email, "SIGNUP")
        if not status["verified"]:
            raise HTTPException(status_code=400, detail="email verification required")
