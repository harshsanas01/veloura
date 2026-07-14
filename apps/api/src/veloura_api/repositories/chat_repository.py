import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from veloura_api.models.chat import ChatMessage, ChatSession
from veloura_api.models.outfit import Outfit, OutfitItem


class ChatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        return self.db.scalar(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.outfits).selectinload(Outfit.items).selectinload(OutfitItem.product),
                selectinload(ChatSession.outfits).selectinload(Outfit.items).selectinload(OutfitItem.variant),
            )
        )

    def create_session(self, user_id: uuid.UUID, title: str) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        self.db.add(session)
        self.db.flush()
        return session

    def list_sessions(self, user_id: uuid.UUID) -> list[ChatSession]:
        return list(
            self.db.scalars(
                select(ChatSession)
                .where(ChatSession.user_id == user_id)
                .order_by(ChatSession.updated_at.desc())
            ).all()
        )

    def add_message(
        self, session_id: uuid.UUID, role, content: str, structured_response: dict | None = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id, role=role, content=content, structured_response=structured_response
        )
        self.db.add(message)
        self.db.flush()
        return message
