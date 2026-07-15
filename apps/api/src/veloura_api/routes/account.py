import uuid

from fastapi import APIRouter, status

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.account import ChangePasswordRequest, DeleteAccountRequest, ProfileUpdateRequest
from veloura_api.schemas.address import AddressCreate, AddressOut, AddressUpdate
from veloura_api.schemas.auth import UserOut
from veloura_api.schemas.style_profile import StyleProfileOut, StyleProfileUpdate
from veloura_api.services.account_service import AccountService

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/profile", response_model=UserOut)
def get_profile(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)


@router.patch("/profile", response_model=UserOut)
def update_profile(payload: ProfileUpdateRequest, current_user: CurrentUser, db: DbSession) -> UserOut:
    user = AccountService(db).update_profile(current_user, payload)
    return UserOut.model_validate(user)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordRequest, current_user: CurrentUser, db: DbSession) -> None:
    AccountService(db).change_password(current_user, payload)


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(payload: DeleteAccountRequest, current_user: CurrentUser, db: DbSession) -> None:
    AccountService(db).delete_account(current_user, payload)


@router.get("/addresses", response_model=list[AddressOut])
def list_addresses(current_user: CurrentUser, db: DbSession) -> list[AddressOut]:
    addresses = AccountService(db).list_addresses(current_user.id)
    return [AddressOut.model_validate(a) for a in addresses]


@router.post("/addresses", response_model=AddressOut, status_code=201)
def create_address(payload: AddressCreate, current_user: CurrentUser, db: DbSession) -> AddressOut:
    address = AccountService(db).create_address(current_user.id, payload)
    return AddressOut.model_validate(address)


@router.patch("/addresses/{address_id}", response_model=AddressOut)
def update_address(
    address_id: uuid.UUID, payload: AddressUpdate, current_user: CurrentUser, db: DbSession
) -> AddressOut:
    address = AccountService(db).update_address(current_user.id, address_id, payload)
    return AddressOut.model_validate(address)


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    AccountService(db).delete_address(current_user.id, address_id)


@router.get("/style-profile", response_model=StyleProfileOut)
def get_style_profile(current_user: CurrentUser, db: DbSession) -> StyleProfileOut:
    profile = AccountService(db).get_style_profile(current_user.id)
    return StyleProfileOut.model_validate(profile)


@router.put("/style-profile", response_model=StyleProfileOut)
def update_style_profile(
    payload: StyleProfileUpdate, current_user: CurrentUser, db: DbSession
) -> StyleProfileOut:
    profile = AccountService(db).update_style_profile(current_user.id, payload)
    return StyleProfileOut.model_validate(profile)
