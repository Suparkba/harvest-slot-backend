from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, instance):
        self.session.add(instance)
        self.session.flush()
        return instance
