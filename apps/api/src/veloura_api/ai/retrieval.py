from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from veloura_api.ai.client import get_embedding
from veloura_api.ai.preferences import StylePreferences
from veloura_api.models.product import Gender, Product, ProductVariant

CANDIDATE_LIMIT = 30


def get_candidate_products(db: Session, preferences: StylePreferences) -> list[Product]:
    """Retrieve real, active, in-stock products from Postgres that plausibly match the
    user's request. The LLM is only ever shown products returned from this function, so it
    is structurally impossible for it to recommend an item that isn't in the catalog."""

    query = (
        select(Product)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .where(Product.is_active.is_(True), ProductVariant.inventory_quantity > 0)
        .options(selectinload(Product.variants), joinedload(Product.category))
        .distinct()
    )

    if preferences.gender_preference in ("men", "women"):
        query = query.where(
            or_(Product.gender == preferences.gender_preference, Product.gender == Gender.UNISEX)
        )

    if preferences.budget:
        # Allow some headroom since a full outfit may combine several items.
        query = query.where(Product.base_price <= preferences.budget)

    candidates = list(db.scalars(query.limit(200)).unique().all())

    query_text = " ".join(
        filter(
            None,
            [
                preferences.occasion,
                preferences.style,
                preferences.season,
                " ".join(preferences.preferred_colors),
            ],
        )
    )
    query_embedding = get_embedding(query_text) if query_text.strip() else None

    scored = [(p, _score(p, preferences)) for p in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    if query_embedding is not None:
        embedded = [p for p in candidates if p.embedding is not None]
        if embedded:
            import numpy as np

            qvec = np.array(query_embedding)

            def cosine(p: Product) -> float:
                pvec = np.array(p.embedding)
                denom = (np.linalg.norm(qvec) * np.linalg.norm(pvec)) or 1e-9
                return float(np.dot(qvec, pvec) / denom)

            embedded.sort(key=cosine, reverse=True)
            top_embedded_ids = {p.id for p in embedded[:CANDIDATE_LIMIT]}
            scored = sorted(
                scored,
                key=lambda pair: (pair[0].id in top_embedded_ids, pair[1]),
                reverse=True,
            )

    return [p for p, _ in scored[:CANDIDATE_LIMIT]]


def _score(product: Product, preferences: StylePreferences) -> float:
    score = 0.0
    tags = set(product.occasion_tags) | set(product.style_tags) | set(product.season_tags)
    tags_lower = {t.lower() for t in tags}

    occasion_slug = preferences.occasion.lower().replace(" ", "-")
    if occasion_slug in tags_lower or preferences.occasion.lower() in tags_lower:
        score += 3

    if preferences.style and preferences.style.lower() in tags_lower:
        score += 2

    if preferences.season and preferences.season.lower() in tags_lower:
        score += 1

    if preferences.required_categories:
        if product.category.slug in preferences.required_categories:
            score += 2

    variant_colors = {v.color_name.lower() for v in product.variants}
    if preferences.preferred_colors:
        if variant_colors & {c.lower() for c in preferences.preferred_colors}:
            score += 2
    if preferences.excluded_colors:
        excluded_lower = {c.lower() for c in preferences.excluded_colors}
        if variant_colors <= excluded_lower:
            score -= 5

    if product.is_featured:
        score += 0.5

    return score
