from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction_scope(session: Session) -> Generator[Session, None, None]:
    if session.in_transaction():
        yield session
        return

    with session.begin():
        yield session
