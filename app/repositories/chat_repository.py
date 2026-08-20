from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.chat import Chat
from app.models.message import Message
from app.models.message_source import MessageSource


class ChatRepository:
    def create_session(self, db: Session, user_id: int, title: str) -> Chat:
        chat = Chat(user_id=user_id, title=title or "New Legal Query")
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    def list_sessions(self, db: Session, user_id: int) -> List[Chat]:
        return (
            db.query(Chat)
            .filter(Chat.user_id == user_id)
            .order_by(Chat.updated_at.desc())
            .all()
        )

    def get_session(self, db: Session, user_id: int, session_id: int) -> Optional[Chat]:
        return (
            db.query(Chat)
            .filter(Chat.id == session_id, Chat.user_id == user_id)
            .first()
        )

    def add_message(
        self,
        db: Session,
        chat_id: int,
        role: str,
        content: str,
        *,
        source_type: Optional[str] = None,
        is_error: bool = False,
        metadata: Optional[Dict] = None,
    ) -> Message:
        message = Message(
            chat_id=chat_id,
            role=role,
            content=content,
            source_type=source_type,
            is_error=is_error,
            metadata_json=metadata,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def add_sources(self, db: Session, message_id: int, sources: List[Dict]) -> None:
        for index, source in enumerate(sources or []):
            db.add(
                MessageSource(
                    message_id=message_id,
                    position=index,
                    title=source.get("title"),
                    source_type=source.get("source_type"),
                    reference=source.get("reference"),
                    content=source.get("content"),
                    metadata_json=source.get("metadata"),
                    distance=source.get("distance"),
                )
            )
        db.commit()

    def touch_session(self, db: Session, chat: Chat) -> None:
        chat.updated_at = func.now()
        db.commit()
        db.refresh(chat)

    def delete_session(self, db: Session, chat: Chat) -> None:
        db.delete(chat)
        db.commit()


chat_repository = ChatRepository()