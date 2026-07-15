import uuid

from fastapi import APIRouter

from veloura_api.dependencies import DbSession
from veloura_api.models.product import Gender
from veloura_api.schemas.product import ProductListItemOut
from veloura_api.services.recommendation_service import RecommendationService

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations/trending", response_model=list[ProductListItemOut])
def trending(db: DbSession, gender: Gender | None = None, limit: int = 8) -> list[ProductListItemOut]:
    return RecommendationService(db).trending(gender=gender, limit=limit)


@router.get("/products/{product_id}/also-bought", response_model=list[ProductListItemOut])
def also_bought(product_id: uuid.UUID, db: DbSession, limit: int = 4) -> list[ProductListItemOut]:
    return RecommendationService(db).also_bought(product_id, limit=limit)


@router.get("/products/{product_id}/complete-the-look", response_model=list[ProductListItemOut])
def complete_the_look(product_id: uuid.UUID, db: DbSession, limit: int = 4) -> list[ProductListItemOut]:
    return RecommendationService(db).complete_the_look(product_id, limit=limit)
