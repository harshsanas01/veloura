import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from veloura_api.models.address import Address


class AddressRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Address]:
        return list(
            self.db.scalars(
                select(Address).where(Address.user_id == user_id).order_by(Address.created_at.desc())
            ).all()
        )

    def get(self, user_id: uuid.UUID, address_id: uuid.UUID) -> Address | None:
        return self.db.scalar(select(Address).where(Address.id == address_id, Address.user_id == user_id))

    def clear_default_shipping(self, user_id: uuid.UUID) -> None:
        for address in self.list_for_user(user_id):
            if address.is_default_shipping:
                address.is_default_shipping = False

    def clear_default_billing(self, user_id: uuid.UUID) -> None:
        for address in self.list_for_user(user_id):
            if address.is_default_billing:
                address.is_default_billing = False
