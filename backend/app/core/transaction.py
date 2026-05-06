from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction_scope(session: Session) -> Generator[Session, None, None]:
    if session.in_nested_transaction():
        yield session
        return

    try:
        yield session
        if session.in_transaction():
            session.commit()
    except Exception:
        if session.in_transaction():
            session.rollback()
        raise
