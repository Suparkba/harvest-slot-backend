from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.core.status import AccountRole, AccountStatus
from backend.app.models.account import Account, CustomerProfile, OwnerProfile
from backend.app.repositories.account_repo import AccountRepository
from backend.app.services.email_verification_service import EmailVerificationService, normalize_email


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = AccountRepository(session)
        self.email_verification_service = EmailVerificationService(session)

    def signup_customer(self, email: str, password: str, name: str, phone: str) -> dict:
        normalized_email = normalize_email(email)
        self.email_verification_service.validate_email_format(normalized_email)
        self.email_verification_service.ensure_verified_for_signup(normalized_email)

        if self.repo.get_by_email(normalized_email):
            raise HTTPException(status_code=400, detail="email already exists")

        account = Account(
            email=normalized_email,
            password_hash=hash_password(password),
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
            email_verified=self.email_verification_service.get_status(normalized_email, "SIGNUP")["verified"],
        )
        self.session.add(account)
        self.session.flush()

        profile = CustomerProfile(
            account_id=account.account_id,
            customer_name=name,
            customer_phone=phone,
        )
        self.session.add(profile)
        self.session.commit()

        return {
            "account_id": account.account_id,
            "customer_id": profile.customer_id,
            "email": account.email,
            "email_verified": account.email_verified,
            "email_verification_required": settings.email_verification_required,
        }

    def signup_owner(self, email: str, password: str, name: str, phone: str) -> dict:
        normalized_email = normalize_email(email)
        self.email_verification_service.validate_email_format(normalized_email)
        self.email_verification_service.ensure_verified_for_signup(normalized_email)

        if self.repo.get_by_email(normalized_email):
            raise HTTPException(status_code=400, detail="email already exists")

        account = Account(
            email=normalized_email,
            password_hash=hash_password(password),
            role=AccountRole.OWNER,
            status=AccountStatus.ACTIVE,
            email_verified=self.email_verification_service.get_status(normalized_email, "SIGNUP")["verified"],
        )
        self.session.add(account)
        self.session.flush()

        profile = OwnerProfile(
            account_id=account.account_id,
            owner_name=name,
            owner_phone=phone,
        )
        self.session.add(profile)
        self.session.commit()

        return {
            "account_id": account.account_id,
            "owner_id": profile.owner_id,
            "email": account.email,
            "email_verified": account.email_verified,
            "email_verification_required": settings.email_verification_required,
        }

    def login(self, email: str, password: str) -> dict:
        normalized_email = normalize_email(email)
        account = self.repo.get_by_email(normalized_email)
        if not account or not verify_password(password, account.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")
        account.last_login_at = datetime.utcnow()
        self.session.commit()
        access_token = create_access_token(subject=account.email, role=account.role)
        return {"access_token": access_token, "token_type": "bearer", "role": account.role}

    def get_me(self, account_id: int) -> dict:
        account = self.repo.get_account(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="account not found")
        customer_profile = None
        owner_profile = None
        if account.customer_profile:
            customer_profile = {
                "customer_id": account.customer_profile.customer_id,
                "customer_name": account.customer_profile.customer_name,
                "customer_phone": account.customer_profile.customer_phone,
                "default_receiver_name": account.customer_profile.default_receiver_name,
                "default_receiver_phone": account.customer_profile.default_receiver_phone,
                "default_shipping_address": account.customer_profile.default_shipping_address,
            }
        if account.owner_profile:
            owner_profile = {
                "owner_id": account.owner_profile.owner_id,
                "owner_name": account.owner_profile.owner_name,
                "owner_phone": account.owner_profile.owner_phone,
                "business_number": account.owner_profile.business_number,
            }
        return {
            "account_id": account.account_id,
            "email": account.email,
            "role": account.role,
            "status": account.status,
            "email_verified": account.email_verified,
            "customer_profile": customer_profile,
            "owner_profile": owner_profile,
        }
