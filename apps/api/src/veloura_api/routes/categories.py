from fastapi import APIRouter
from sqlalchemy import select

from veloura_api.dependencies import DbSession
from veloura_api.models.category import Category
from veloura_api.schemas.category import CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: DbSession) -> list[CategoryOut]:
    categories = db.scalars(select(Category).order_by(Category.name)).all()
    return [CategoryOut.model_validate(c) for c in categories]
