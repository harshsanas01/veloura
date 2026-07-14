import re
import uuid


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def embedding_text(*, name: str, description: str, category: str, gender: str,
                    style_tags: list[str], occasion_tags: list[str], season_tags: list[str],
                    colors: list[str]) -> str:
    parts = [
        name,
        description,
        f"category: {category}",
        f"gender: {gender}",
        f"style: {', '.join(style_tags)}",
        f"occasions: {', '.join(occasion_tags)}",
        f"season: {', '.join(season_tags)}",
        f"colors: {', '.join(colors)}",
    ]
    return " | ".join(p for p in parts if p)
