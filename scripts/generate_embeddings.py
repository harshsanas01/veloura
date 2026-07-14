"""Backfill pgvector embeddings for products that don't have one yet.

Safe to re-run: only products with a NULL embedding are processed. Requires
OPENAI_API_KEY to be set - if it isn't, this exits early with a clear message
instead of failing, since embeddings are an enhancement (semantic search
ranking) on top of the SQL-filterable AI stylist retrieval, not a hard
requirement for the app to function.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

from sqlalchemy import select
from veloura_api.ai.client import get_embedding
from veloura_api.config import get_settings
from veloura_api.database import SessionLocal
from veloura_api.models.product import Product
from veloura_api.utils import embedding_text


def main() -> None:
    settings = get_settings()
    if not settings.is_ai_enabled:
        print("OPENAI_API_KEY is not set - skipping embedding generation.")
        return

    db = SessionLocal()
    try:
        products = db.scalars(
            select(Product).where(Product.embedding.is_(None), Product.is_active.is_(True))
        ).all()
        print(f"Found {len(products)} products missing embeddings.")

        for i, product in enumerate(products, start=1):
            colors = list({v.color_name for v in product.variants})
            text = embedding_text(
                name=product.name,
                description=product.description,
                category=product.category.slug if product.category else "",
                gender=product.gender.value,
                style_tags=product.style_tags,
                occasion_tags=product.occasion_tags,
                season_tags=product.season_tags,
                colors=colors,
            )
            embedding = get_embedding(text)
            if embedding is not None:
                product.embedding = embedding
            if i % 20 == 0:
                db.commit()
                print(f"  ...{i}/{len(products)}")

        db.commit()
        print("Embedding generation complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
