from pydantic import BaseModel, ConfigDict, Field


class StyleProfileUpdate(BaseModel):
    gender_presentation: str | None = None
    preferred_colors: list[str] | None = None
    disliked_colors: list[str] | None = None
    preferred_styles: list[str] | None = None
    favorite_occasions: list[str] | None = None
    preferred_brands: list[str] | None = None
    sizes: dict[str, str] | None = None
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)


class StyleProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gender_presentation: str | None
    preferred_colors: list[str]
    disliked_colors: list[str]
    preferred_styles: list[str]
    favorite_occasions: list[str]
    preferred_brands: list[str]
    sizes: dict
    budget_min: int | None
    budget_max: int | None
