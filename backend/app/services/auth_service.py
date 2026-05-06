from datetime import datetime, timedelta
from random import randint

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.core.status import AccountRole, AccountStatus, EmailVerificationPurpose
from backend.app.models.account import Account, CustomerProfile, EmailVerification, OwnerProfile
from backend.app.repositories.account_repo import AccountRepository


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = AccountRepository(session)

    def _create_email_verification(self, account: Account, purpose: str) -> EmailVerification:
        verification = EmailVerification(
            account_id=account.account_id,
            email=account.email,
            purpose=purpose,
            verification_code=f"{randint(100000, 999999)}",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            verified=False,
        )
        self.session.add(verification)
        self.session.flush()
        return verification

    def signup_customer(self, email: str, password: str, name: str, phone: str) -> dict:
        if self.repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="email already exists")

        account = Account(
            email=email,
            password_hash=hash_password(password),
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
        )
        self.session.add(account)
        self.session.flush()

        profile = CustomerProfile(
            account_id=account.account_id,
            customer_name=name,
            customer_phone=phone,
        )
        self.session.add(profile)
        verification = self._create_email_verification(account, EmailVerificationPurpose.SIGNUP)
        self.session.commit()

        return {
            "account_id": account.account_id,
            "customer_id": profile.customer_id,
            "email": account.email,
            "mock_verification_code": verification.verification_code,
        }

    def signup_owner(self, email: str, password: str, name: str, phone: str) -> dict:
        if self.repo.get_by_email(email):
            raise HTTPException(status_code=400, detail="email already exists")

        account = Account(
            email=email,
            password_hash=hash_password(password),
            role=AccountRole.OWNER,
            status=AccountStatus.ACTIVE,
        )
        self.session.add(account)
        self.session.flush()

        profile = OwnerProfile(
            account_id=account.account_id,
            owner_name=name,
            owner_phone=phone,
        )
        self.session.add(profile)
        verification = self._create_email_verification(account, EmailVerificationPurpose.SIGNUP)
        self.session.commit()

        return {
            "account_id": account.account_id,
            "owner_id": profile.owner_id,
            "email": account.email,
            "mock_verification_code": verification.verification_code,
        }

    def resend_verification(self, email: str, purpose: str) -> dict:
        account = self.repo.get_by_email(email)
        if not account:
            raise HTTPException(status_code=404, detail="account not found")
        verification = self._create_email_verification(account, purpose)
        self.session.commit()
        return {"email": email, "purpose": purpose, "mock_verification_code": verification.verification_code}

    def verify_email(self, email: str, verification_code: str) -> dict:
        verification = self.repo.get_email_verification(email, EmailVerificationPurpose.SIGNUP)
        if not verification or verification.verification_code != verification_code:
            raise HTTPException(status_code=400, detail="invalid verification code")
        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="verification code expired")

        verification.verified = True
        verification.verified_at = datetime.utcnow()
        account = self.repo.get_account(verification.account_id)
        if account:
            account.email_verified = True
        self.session.commit()
        return {"email": email, "verified": True}

    def login(self, email: str, password: str) -> dict:
        account = self.repo.get_by_email(email)
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
