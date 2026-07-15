import uuid

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = None
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=30)
    is_default_shipping: bool = False
    is_default_billing: bool = False


class AddressUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    line1: str | None = Field(default=None, min_length=1, max_length=255)
    line2: str | None = None
    city: str | None = Field(default=None, min_length=1, max_length=120)
    state: str | None = Field(default=None, min_length=1, max_length=120)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=1, max_length=30)
    is_default_shipping: bool | None = None
    is_default_billing: bool | None = None


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    line1: str
    line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    phone: str
    is_default_shipping: bool
    is_default_billing: bool
