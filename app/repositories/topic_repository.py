from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.topic import Topic
from app.schemas.topic import TopicCreate, TopicUpdate


class TopicRepository(CRUDBase[Topic, TopicCreate, TopicUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Optional[Topic]:
        return db.query(Topic).filter(Topic.slug == slug).first()


topic_repository = TopicRepository(Topic)