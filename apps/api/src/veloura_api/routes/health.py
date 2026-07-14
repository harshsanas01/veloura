from fastapi import APIRouter
from sqlalchemy import text

from veloura_api.dependencies import DbSession

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: DbSession) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "veloura-api"}
