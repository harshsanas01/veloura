import re

from pydantic import BaseModel, Field

from veloura_api.ai.client import get_openai_client
from veloura_api.config import get_settings

COLOR_WORDS = [
    "black",
    "white",
    "navy",
    "blue",
    "red",
    "green",
    "olive",
    "beige",
    "cream",
    "tan",
    "brown",
    "grey",
    "gray",
    "pink",
    "purple",
    "burgundy",
    "yellow",
    "orange",
    "khaki",
    "denim",
    "charcoal",
    "ivory",
]

OCCASION_KEYWORDS = {
    "pool party": ["pool party", "pool"],
    "date night": ["date night", "date"],
    "wedding": ["wedding"],
    "business casual": ["business casual", "office", "work"],
    "vacation": ["vacation", "holiday", "trip"],
    "party": ["party"],
    "casual": ["casual", "everyday", "weekend"],
    "formal": ["formal", "black tie", "gala"],
}


class StylePreferences(BaseModel):
    occasion: str = Field(description="The event or occasion the user is dressing for.")
    gender_preference: str | None = Field(default=None, description="'men', 'women', or null if unspecified.")
    preferred_colors: list[str] = Field(default_factory=list)
    excluded_colors: list[str] = Field(default_factory=list)
    style: str = Field(default="casual", description="e.g. casual, formal, business-casual, streetwear")
    season: str | None = Field(default=None)
    budget: float | None = Field(default=None, description="Maximum total outfit budget in USD.")
    required_categories: list[str] = Field(default_factory=list)
    size_preferences: dict[str, str] = Field(default_factory=dict)
    preferred_brands: list[str] = Field(default_factory=list)
    excluded_brands: list[str] = Field(default_factory=list)
    anchor_product_id: str | None = Field(
        default=None,
        description="A specific product ID (e.g. from the user's cart) to build the outfit around.",
    )
    additional_notes: str = Field(default="")


def _heuristic_extract(message: str) -> StylePreferences:
    lower = message.lower()

    occasion = "everyday"
    for canonical, keywords in OCCASION_KEYWORDS.items():
        if any(k in lower for k in keywords):
            occasion = canonical
            break

    gender = None
    if re.search(r"\b(men|man|guy|male|his)\b", lower):
        gender = "men"
    elif re.search(r"\b(women|woman|girl|female|her)\b", lower):
        gender = "women"

    excluded_colors = []
    preferred_colors = []
    for color in COLOR_WORDS:
        if re.search(rf"no {color}|not {color}|without {color}", lower):
            excluded_colors.append(color)
        elif re.search(rf"\b{color}\b", lower):
            preferred_colors.append(color)

    budget = None
    budget_match = re.search(r"\$?\s?(\d{2,4})\s?(dollars|usd|budget)?", lower)
    if "under" in lower or "budget" in lower or "$" in message:
        if budget_match:
            budget = float(budget_match.group(1))

    style = "casual"
    if "formal" in lower or "black tie" in lower:
        style = "formal"
    elif "business" in lower or "office" in lower:
        style = "business-casual"
    elif "street" in lower:
        style = "streetwear"
    elif "minimal" in lower:
        style = "minimal"
    elif "all-black" in lower or "all black" in lower:
        style = "all-black"

    season = None
    for s in ["summer", "winter", "spring", "fall", "autumn"]:
        if s in lower:
            season = "fall" if s == "autumn" else s
            break

    return StylePreferences(
        occasion=occasion,
        gender_preference=gender,
        preferred_colors=preferred_colors,
        excluded_colors=excluded_colors,
        style=style,
        season=season,
        budget=budget,
        additional_notes=message,
    )


EXTRACTION_SYSTEM_PROMPT = """You are a fashion preference extraction engine for Veloura, a \
premium clothing retailer. Read the customer's styling request (and any prior conversation \
turns) and extract structured shopping preferences. Only extract what is stated or strongly \
implied - do not invent a budget, colors, or occasion that were never mentioned. If gender is \
not specified, leave gender_preference null."""


def extract_preferences(message: str, history: list[str] | None = None) -> StylePreferences:
    client = get_openai_client()
    if client is None:
        return _heuristic_extract(message)

    settings = get_settings()
    context = "\n".join(history or [])
    user_prompt = f"Conversation so far:\n{context}\n\nLatest request: {message}" if context else message

    try:
        completion = client.beta.chat.completions.parse(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=StylePreferences,
            temperature=0.2,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is not None:
            return parsed
    except Exception:
        pass
    return _heuristic_extract(message)
