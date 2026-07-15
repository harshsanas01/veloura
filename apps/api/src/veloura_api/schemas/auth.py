import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from veloura_api.models.user import UserRole

COMMON_WEAK_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "12345678",
    "123456789",
    "qwerty123",
    "letmein1",
    "welcome1",
    "admin123",
    "iloveyou",
    "monkey123",
    "football1",
    "abc12345",
    "changeme",
    "passw0rd",
    "trustno1",
    "sunshine1",
    "princess1",
}


def validate_password_strength(password: str, *, email: str | None = None) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must include at least one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must include at least one special character.")
    if password.lower() in COMMON_WEAK_PASSWORDS:
        raise ValueError("This password is too common. Please choose a stronger password.")
    if email and password.lower() == email.lower():
        raise ValueError("Password must not be the same as your email.")
    return password


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(default="", max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def check_password(self) -> "RegisterRequest":
        validate_password_strength(self.password, email=self.email)
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
