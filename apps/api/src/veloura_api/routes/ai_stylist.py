import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.ai import (
    ChatSessionDetailOut,
    ChatSessionSummaryOut,
    FeedbackRequest,
    StylistChatRequest,
    StylistResponseOut,
)
from veloura_api.services.ai_stylist_service import AIStylistService

router = APIRouter(prefix="/ai-stylist", tags=["ai-stylist"])


@router.post("/recommend", response_model=StylistResponseOut)
def recommend(payload: StylistChatRequest, current_user: CurrentUser, db: DbSession) -> StylistResponseOut:
    return AIStylistService(db).recommend(current_user.id, payload)


@router.get("/sessions", response_model=list[ChatSessionSummaryOut])
def list_sessions(current_user: CurrentUser, db: DbSession) -> list[ChatSessionSummaryOut]:
    return AIStylistService(db).list_sessions(current_user.id)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut)
def get_session(session_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> ChatSessionDetailOut:
    return AIStylistService(db).get_session(current_user.id, session_id)


@router.post("/feedback", status_code=204)
def submit_feedback(payload: FeedbackRequest, current_user: CurrentUser, db: DbSession) -> None:
    AIStylistService(db).submit_feedback(current_user.id, payload)
