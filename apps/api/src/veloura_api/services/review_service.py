import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from veloura_api.models.review import Review, ReviewHelpfulness
from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.repositories.review_repository import ReviewRepository
from veloura_api.schemas.review import (
    RatingDistribution,
    ReviewCreate,
    ReviewListResponse,
    ReviewOut,
    ReviewUpdate,
)


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReviewRepository(db)
        self.products = ProductRepository(db)

    def _to_out(self, review: Review, *, current_user_id: uuid.UUID | None) -> ReviewOut:
        return ReviewOut(
            id=review.id,
            product_id=review.product_id,
            user_id=review.user_id,
            author_name=review.user.first_name if review.user else "Veloura Customer",
            rating=review.rating,
            title=review.title,
            body=review.body,
            fit_feedback=review.fit_feedback,
            size_purchased=review.size_purchased,
            is_verified_purchase=review.is_verified_purchase,
            is_active=review.is_active,
            helpful_count=self.repo.helpful_count(review.id),
            helpful_by_me=(
                self.repo.user_marked_helpful(review.id, current_user_id)
                if current_user_id
                else False
            ),
            is_mine=review.user_id == current_user_id if current_user_id else False,
            created_at=review.created_at,
        )

    def list_for_product(
        self, product_id: uuid.UUID, *, sort: str, current_user_id: uuid.UUID | None
    ) -> ReviewListResponse:
        reviews = self.repo.list_for_product(product_id, sort=sort)
        items = [self._to_out(r, current_user_id=current_user_id) for r in reviews]

        total = len(items)
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for r in reviews:
            distribution[r.rating] += 1
        average = round(sum(r.rating for r in reviews) / total, 2) if total else 0.0

        return ReviewListResponse(
            items=items,
            total=total,
            average_rating=average,
            distribution=RatingDistribution(
                one=distribution[1],
                two=distribution[2],
                three=distribution[3],
                four=distribution[4],
                five=distribution[5],
            ),
        )

    def create_review(
        self, product_id: uuid.UUID, user_id: uuid.UUID, payload: ReviewCreate
    ) -> ReviewOut:
        product = self.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if self.repo.get_by_product_and_user(product_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You've already reviewed this product. You can edit your existing review instead.",
            )

        review = Review(
            product_id=product_id,
            user_id=user_id,
            rating=payload.rating,
            title=payload.title,
            body=payload.body,
            fit_feedback=payload.fit_feedback,
            size_purchased=payload.size_purchased,
            is_verified_purchase=self.repo.has_purchased(product_id, user_id),
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return self._to_out(review, current_user_id=user_id)

    def update_review(
        self, review_id: uuid.UUID, user_id: uuid.UUID, payload: ReviewUpdate
    ) -> ReviewOut:
        review = self.repo.get_by_id(review_id)
        if not review or review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(review, field, value)
        self.db.commit()
        self.db.refresh(review)
        return self._to_out(review, current_user_id=user_id)

    def delete_review(self, review_id: uuid.UUID, user_id: uuid.UUID) -> None:
        review = self.repo.get_by_id(review_id)
        if not review or review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
        self.db.delete(review)
        self.db.commit()

    def toggle_helpful(self, review_id: uuid.UUID, user_id: uuid.UUID) -> ReviewOut:
        review = self.repo.get_by_id(review_id)
        if not review or not review.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
        existing = self.db.scalar(
            select(ReviewHelpfulness).where(
                ReviewHelpfulness.review_id == review_id, ReviewHelpfulness.user_id == user_id
            )
        )
        if existing:
            self.db.delete(existing)
        else:
            self.db.add(ReviewHelpfulness(review_id=review_id, user_id=user_id))
        self.db.commit()
        return self._to_out(review, current_user_id=user_id)

    def moderate(self, review_id: uuid.UUID, is_active: bool) -> ReviewOut:
        review = self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
        review.is_active = is_active
        self.db.commit()
        self.db.refresh(review)
        return self._to_out(review, current_user_id=None)

    def list_all_for_admin(self) -> list[ReviewOut]:
        reviews = self.db.scalars(
            select(Review).options(joinedload(Review.user)).order_by(Review.created_at.desc())
        ).all()
        return [self._to_out(r, current_user_id=None) for r in reviews]
