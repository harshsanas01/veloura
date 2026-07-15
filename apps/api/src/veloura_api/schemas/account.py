from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from veloura_api.schemas.auth import validate_password_strength


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value else value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_new_password(self) -> "ChangePasswordRequest":
        validate_password_strength(self.new_password)
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")
        if self.new_password == self.current_password:
            raise ValueError("New password must be different from your current password.")
        return self


class DeleteAccountRequest(BaseModel):
    password: str
    confirm: bool

    @field_validator("confirm")
    @classmethod
    def must_confirm(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must confirm account deletion.")
        return value
