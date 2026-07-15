import uuid

from fastapi import APIRouter, status

from veloura_api.dependencies import CurrentUser, DbSession, OptionalCurrentUser
from veloura_api.schemas.review import (
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewSortOption,
    ReviewUpdate,
)
from veloura_api.services.review_service import ReviewService

router = APIRouter(tags=["reviews"])


@router.get("/products/{product_id}/reviews", response_model=ReviewListResponse)
def list_reviews(
    product_id: uuid.UUID,
    db: DbSession,
    current_user: OptionalCurrentUser,
    sort: ReviewSortOption = ReviewSortOption.NEWEST,
) -> ReviewListResponse:
    current_user_id = current_user.id if current_user else None
    return ReviewService(db).list_for_product(product_id, sort=sort.value, current_user_id=current_user_id)


@router.post("/products/{product_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    product_id: uuid.UUID, payload: ReviewCreate, current_user: CurrentUser, db: DbSession
) -> ReviewOut:
    return ReviewService(db).create_review(product_id, current_user.id, payload)


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(
    review_id: uuid.UUID, payload: ReviewUpdate, current_user: CurrentUser, db: DbSession
) -> ReviewOut:
    return ReviewService(db).update_review(review_id, current_user.id, payload)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    ReviewService(db).delete_review(review_id, current_user.id)


@router.post("/reviews/{review_id}/helpful", response_model=ReviewOut)
def toggle_helpful(review_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> ReviewOut:
    return ReviewService(db).toggle_helpful(review_id, current_user.id)
