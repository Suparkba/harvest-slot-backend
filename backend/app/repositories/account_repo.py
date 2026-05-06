from sqlalchemy import desc, select

from backend.app.models.account import Account, CustomerProfile, EmailVerification, OwnerProfile
from backend.app.repositories.base_repo import BaseRepository


class AccountRepository(BaseRepository):
    def get_by_email(self, email: str) -> Account | None:
        return self.session.scalar(select(Account).where(Account.email == email))

    def get_account(self, account_id: int) -> Account | None:
        return self.session.get(Account, account_id)

    def get_customer_profile(self, account_id: int) -> CustomerProfile | None:
        return self.session.scalar(select(CustomerProfile).where(CustomerProfile.account_id == account_id))

    def get_owner_profile(self, account_id: int) -> OwnerProfile | None:
        return self.session.scalar(select(OwnerProfile).where(OwnerProfile.account_id == account_id))

    def get_email_verification(self, email: str, purpose: str) -> EmailVerification | None:
        stmt = (
            select(EmailVerification)
            .where(EmailVerification.email == email, EmailVerification.purpose == purpose)
            .order_by(desc(EmailVerification.created_at))
        )
        return self.session.scalar(stmt)
