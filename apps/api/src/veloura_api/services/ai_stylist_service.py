import re
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from veloura_api.ai.outfit_generation import generate_outfits, resolve_outfit_pricing
from veloura_api.ai.preferences import StylePreferences, extract_preferences
from veloura_api.ai.refinement import apply_refinement, detect_refinement
from veloura_api.ai.retrieval import get_candidate_products
from veloura_api.models.chat import ChatRole
from veloura_api.models.feedback import RecommendationFeedback
from veloura_api.models.outfit import Outfit, OutfitItem
from veloura_api.models.style_profile import StyleProfile
from veloura_api.repositories.cart_repository import CartRepository
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

REFINEMENT_SUMMARIES = {
    "cheaper": "Here's a more budget-friendly version of your look.",
    "more_formal": "Dressed up your look for a more polished feel.",
    "more_casual": "Relaxed your look for something more casual.",
    "change_color": "Updated the color of your look.",
    "replace_item": "Swapped in a fresh alternative for that piece.",
}


class AIStylistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ChatRepository(db)
        self.carts = CartRepository(db)

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
        preferences = self._apply_user_context(preferences, user_id, payload.message)
        candidates = get_candidate_products(self.db, preferences)

        if payload.session_id and session.outfits:
            refined = self._try_refine_last_outfit(session, payload.message, candidates)
            if refined is not None:
                self.db.commit()
                return refined

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

    def _apply_user_context(
        self, preferences: StylePreferences, user_id: uuid.UUID, message: str
    ) -> StylePreferences:
        """Fills in gaps the message didn't specify using the user's saved style
        profile, and - if they reference their cart - anchors the outfit around
        whatever they most recently added. Never overrides something the user
        explicitly said in this message."""
        updates: dict = {}

        profile = self.db.scalar(select(StyleProfile).where(StyleProfile.user_id == user_id))
        if profile:
            if not preferences.preferred_colors and profile.preferred_colors:
                updates["preferred_colors"] = profile.preferred_colors
            if profile.disliked_colors:
                updates["excluded_colors"] = list(
                    {*preferences.excluded_colors, *profile.disliked_colors}
                )
            if not preferences.budget and profile.budget_max:
                updates["budget"] = float(profile.budget_max)
            if not preferences.gender_preference and profile.gender_presentation in ("men", "women"):
                updates["gender_preference"] = profile.gender_presentation
            if profile.preferred_brands:
                updates["preferred_brands"] = profile.preferred_brands

        if re.search(r"\bcart\b", message.lower()):
            cart = self.carts.get_or_create_for_user(user_id)
            if cart.items:
                most_recent = max(cart.items, key=lambda i: i.created_at)
                updates["anchor_product_id"] = str(most_recent.variant.product_id)

        return preferences.model_copy(update=updates) if updates else preferences

    def _try_refine_last_outfit(self, session, message: str, candidates) -> StylistResponseOut | None:
        """Handles explicit refinement commands ('make it cheaper', 'replace the
        shoes', ...) as a deterministic edit of the most recent outfit in this
        session, rather than a full regeneration. Returns None if no refinement
        was requested or it couldn't be applied, so the caller falls back to
        normal generation."""
        intent = detect_refinement(message)
        if intent is None:
            return None

        last_outfit = max(session.outfits, key=lambda o: o.created_at)
        current_items = [(item.product, item.variant) for item in last_outfit.items]
        if not current_items:
            return None

        refined = apply_refinement(intent, current_items, candidates)
        if refined is None:
            return None

        total_price = round(sum(product.effective_price for product, _, _ in refined), 2)
        new_outfit = Outfit(
            session_id=session.id,
            user_id=last_outfit.user_id,
            name=last_outfit.name,
            explanation=REFINEMENT_SUMMARIES[intent.action.value],
            total_price=total_price,
        )
        self.db.add(new_outfit)
        self.db.flush()

        items_out = []
        for product, variant, reason in refined:
            self.db.add(
                OutfitItem(
                    outfit_id=new_outfit.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    reason=reason,
                )
            )
            items_out.append(
                StylistOutfitItemOut(
                    product_id=product.id,
                    variant_id=variant.id,
                    reason=reason,
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

        summary = REFINEMENT_SUMMARIES[intent.action.value]
        outfit_out = StylistOutfitOut(
            id=new_outfit.id,
            name=new_outfit.name,
            explanation=summary,
            total_price=total_price,
            items=items_out,
        )
        follow_ups = ["Make it cheaper", "Make it more formal", "Change the color", "Replace the shoes"]

        self.repo.add_message(
            session.id,
            ChatRole.ASSISTANT,
            summary,
            structured_response={
                "summary": summary,
                "outfits": [outfit_out.model_dump(mode="json")],
                "follow_up_suggestions": follow_ups,
            },
        )

        return StylistResponseOut(
            session_id=session.id,
            summary=summary,
            outfits=[outfit_out],
            follow_up_suggestions=follow_ups,
        )

    def list_sessions(self, user_id: uuid.UUID) -> list[ChatSessionSummaryOut]:
        sessions = self.repo.list_sessions(user_id)
        return [
            ChatSessionSummaryOut(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at)
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
                ChatMessageOut(id=m.id, role=m.role.value, content=m.content, created_at=m.created_at)
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
