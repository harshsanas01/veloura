import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.ai.outfit_generation import generate_outfits, resolve_outfit_pricing
from veloura_api.ai.preferences import extract_preferences
from veloura_api.ai.retrieval import get_candidate_products
from veloura_api.models.chat import ChatRole
from veloura_api.models.feedback import RecommendationFeedback
from veloura_api.models.outfit import Outfit, OutfitItem
from veloura_api.repositories.chat_repository import ChatRepository
from veloura_api.schemas.ai import (
    ChatMessageOut,
    ChatSessionDetailOut,
    ChatSessionSummaryOut,
    FeedbackRequest,
    StylistChatRequest,
    StylistOutfitItemOut,
    StylistOutfitOut,
    StylistResponseOut,
)

MAX_HISTORY_MESSAGES = 6


class AIStylistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ChatRepository(db)

    def recommend(self, user_id: uuid.UUID, payload: StylistChatRequest) -> StylistResponseOut:
        if payload.session_id:
            session = self.repo.get_session(payload.session_id, user_id)
            if not session:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        else:
            title = payload.message[:60] or "New styling session"
            session = self.repo.create_session(user_id, title)

        history_messages = session.messages[-MAX_HISTORY_MESSAGES:] if payload.session_id else []
        history_texts = [f"{m.role.value}: {m.content}" for m in history_messages]
        llm_history = [
            {"role": "user" if m.role == ChatRole.USER else "assistant", "content": m.content}
            for m in history_messages
        ]

        self.repo.add_message(session.id, ChatRole.USER, payload.message)

        preferences = extract_preferences(payload.message, history_texts)
        candidates = get_candidate_products(self.db, preferences)
        llm_response = generate_outfits(candidates, preferences, llm_history)

        product_map = {str(p.id): p for p in candidates}
        variant_map = {str(v.id): v for p in candidates for v in p.variants}

        outfit_outs: list[StylistOutfitOut] = []
        for outfit in llm_response.outfits:
            total_price = resolve_outfit_pricing(outfit, candidates)
            db_outfit = Outfit(
                session_id=session.id,
                user_id=user_id,
                name=outfit.name,
                explanation=outfit.explanation,
                total_price=total_price,
            )
            self.db.add(db_outfit)
            self.db.flush()

            items_out = []
            for item in outfit.items:
                product = product_map[item.product_id]
                variant = variant_map[item.variant_id]
                self.db.add(
                    OutfitItem(
                        outfit_id=db_outfit.id,
                        product_id=product.id,
                        variant_id=variant.id,
                        reason=item.reason,
                    )
                )
                items_out.append(
                    StylistOutfitItemOut(
                        product_id=product.id,
                        variant_id=variant.id,
                        reason=item.reason,
                        product_name=product.name,
                        product_slug=product.slug,
                        brand=product.brand,
                        image_url=variant.image_url,
                        price=product.effective_price,
                        size=variant.size,
                        color_name=variant.color_name,
                        color_hex=variant.color_hex,
                    )
                )
            outfit_outs.append(
                StylistOutfitOut(
                    id=db_outfit.id,
                    name=outfit.name,
                    explanation=outfit.explanation,
                    total_price=total_price,
                    items=items_out,
                )
            )

        self.repo.add_message(
            session.id,
            ChatRole.ASSISTANT,
            llm_response.summary,
            structured_response=llm_response.model_dump(mode="json"),
        )
        self.db.commit()

        return StylistResponseOut(
            session_id=session.id,
            summary=llm_response.summary,
            outfits=outfit_outs,
            follow_up_suggestions=llm_response.follow_up_suggestions,
        )

    def list_sessions(self, user_id: uuid.UUID) -> list[ChatSessionSummaryOut]:
        sessions = self.repo.list_sessions(user_id)
        return [
            ChatSessionSummaryOut(
                id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at
            )
            for s in sessions
        ]

    def get_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> ChatSessionDetailOut:
        session = self.repo.get_session(session_id, user_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        outfits_out = []
        for outfit in session.outfits:
            items_out = [
                StylistOutfitItemOut(
                    product_id=item.product.id,
                    variant_id=item.variant.id,
                    reason=item.reason,
                    product_name=item.product.name,
                    product_slug=item.product.slug,
                    brand=item.product.brand,
                    image_url=item.variant.image_url,
                    price=item.product.effective_price,
                    size=item.variant.size,
                    color_name=item.variant.color_name,
                    color_hex=item.variant.color_hex,
                )
                for item in outfit.items
            ]
            outfits_out.append(
                StylistOutfitOut(
                    id=outfit.id,
                    name=outfit.name,
                    explanation=outfit.explanation,
                    total_price=float(outfit.total_price),
                    items=items_out,
                )
            )

        return ChatSessionDetailOut(
            id=session.id,
            title=session.title,
            messages=[
                ChatMessageOut(
                    id=m.id, role=m.role.value, content=m.content, created_at=m.created_at
                )
                for m in session.messages
            ],
            outfits=outfits_out,
        )

    def submit_feedback(self, user_id: uuid.UUID, payload: FeedbackRequest) -> None:
        outfit = self.db.get(Outfit, payload.outfit_id)
        if not outfit or outfit.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found.")
        self.db.add(
            RecommendationFeedback(
                user_id=user_id,
                outfit_id=payload.outfit_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        )
        self.db.commit()
