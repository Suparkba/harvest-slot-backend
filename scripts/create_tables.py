"""MVP local test helper.

Production schema application should prefer the official
`harvest-slot-docs-local/assets/10_schema_mysql.sql` DDL.
"""

from backend.app.core.database import Base, engine
from backend.app import models  # noqa: F401


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("SQLAlchemy metadata create_all completed.")


if __name__ == "__main__":
    main()
