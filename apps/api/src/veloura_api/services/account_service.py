import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from veloura_api.models.address import Address
from veloura_api.models.style_profile import StyleProfile
from veloura_api.models.user import User
from veloura_api.repositories.address_repository import AddressRepository
from veloura_api.repositories.user_repository import UserRepository
from veloura_api.schemas.account import ChangePasswordRequest, DeleteAccountRequest, ProfileUpdateRequest
from veloura_api.schemas.address import AddressCreate, AddressUpdate
from veloura_api.schemas.style_profile import StyleProfileUpdate
from veloura_api.security import hash_password, verify_password


class AccountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.addresses = AddressRepository(db)

    # -- profile ------------------------------------------------------------
    def update_profile(self, user: User, payload: ProfileUpdateRequest) -> User:
        if payload.email and payload.email != user.email:
            existing = self.users.get_by_email(payload.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists.",
                )
            user.email = payload.email
        if payload.first_name is not None:
            user.first_name = payload.first_name
        if payload.last_name is not None:
            user.last_name = payload.last_name
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(self, user: User, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect."
            )
        user.hashed_password = hash_password(payload.new_password)
        self.db.commit()

    def delete_account(self, user: User, payload: DeleteAccountRequest) -> None:
        if not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Password is incorrect.")
        self.db.delete(user)
        self.db.commit()

    # -- addresses ------------------------------------------------------------
    def list_addresses(self, user_id: uuid.UUID) -> list[Address]:
        return self.addresses.list_for_user(user_id)

    def create_address(self, user_id: uuid.UUID, payload: AddressCreate) -> Address:
        if payload.is_default_shipping:
            self.addresses.clear_default_shipping(user_id)
        if payload.is_default_billing:
            self.addresses.clear_default_billing(user_id)
        address = Address(user_id=user_id, **payload.model_dump())
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def update_address(self, user_id: uuid.UUID, address_id: uuid.UUID, payload: AddressUpdate) -> Address:
        address = self.addresses.get(user_id, address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
        data = payload.model_dump(exclude_unset=True)
        if data.get("is_default_shipping"):
            self.addresses.clear_default_shipping(user_id)
        if data.get("is_default_billing"):
            self.addresses.clear_default_billing(user_id)
        for field, value in data.items():
            setattr(address, field, value)
        self.db.commit()
        self.db.refresh(address)
        return address

    def delete_address(self, user_id: uuid.UUID, address_id: uuid.UUID) -> None:
        address = self.addresses.get(user_id, address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
        self.db.delete(address)
        self.db.commit()

    # -- style profile --------------------------------------------------------
    def get_style_profile(self, user_id: uuid.UUID) -> StyleProfile:
        profile = self.db.scalar(select(StyleProfile).where(StyleProfile.user_id == user_id))
        if not profile:
            profile = StyleProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_style_profile(self, user_id: uuid.UUID, payload: StyleProfileUpdate) -> StyleProfile:
        profile = self.get_style_profile(user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile
