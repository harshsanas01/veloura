import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from veloura_api.models.review import FitFeedback


class ReviewSortOption(str, Enum):
    NEWEST = "newest"
    HIGHEST = "highest"
    LOWEST = "lowest"
    MOST_HELPFUL = "most_helpful"


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)
    fit_feedback: FitFeedback | None = None
    size_purchased: str | None = Field(default=None, max_length=20)


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, min_length=1, max_length=5000)
    fit_feedback: FitFeedback | None = None
    size_purchased: str | None = Field(default=None, max_length=20)


class ReviewOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    user_id: uuid.UUID
    author_name: str
    rating: int
    title: str
    body: str
    fit_feedback: FitFeedback | None
    size_purchased: str | None
    is_verified_purchase: bool
    is_active: bool
    helpful_count: int
    helpful_by_me: bool
    is_mine: bool
    created_at: datetime


class RatingDistribution(BaseModel):
    one: int
    two: int
    three: int
    four: int
    five: int


class ReviewListResponse(BaseModel):
    items: list[ReviewOut]
    total: int
    average_rating: float
    distribution: RatingDistribution


class AdminReviewModerateRequest(BaseModel):
    is_active: bool
