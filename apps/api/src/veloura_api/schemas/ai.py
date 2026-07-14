import uuid
from datetime import datetime

from pydantic import BaseModel

from veloura_api.models.feedback import FeedbackRating


class StylistChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID | None = None


class StylistOutfitItemOut(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID
    reason: str
    product_name: str
    product_slug: str
    brand: str
    image_url: str
    price: float
    size: str
    color_name: str
    color_hex: str


class StylistOutfitOut(BaseModel):
    id: uuid.UUID | None = None
    name: str
    explanation: str
    total_price: float
    items: list[StylistOutfitItemOut]


class StylistResponseOut(BaseModel):
    session_id: uuid.UUID
    summary: str
    outfits: list[StylistOutfitOut]
    follow_up_suggestions: list[str]


class ChatMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class ChatSessionSummaryOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    messages: list[ChatMessageOut]
    outfits: list[StylistOutfitOut]


class FeedbackRequest(BaseModel):
    outfit_id: uuid.UUID
    rating: FeedbackRating
    comment: str | None = None
