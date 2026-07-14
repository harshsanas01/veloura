from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.models.cart import Cart
from veloura_api.models.user import User, UserRole
from veloura_api.models.wishlist import Wishlist
from veloura_api.repositories.user_repository import UserRepository
from veloura_api.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, *, email: str, password: str, full_name: str) -> tuple[User, str]:
        if self.users.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists."
            )
        user = self.users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.CUSTOMER,
        )
        self.db.add(Cart(user_id=user.id))
        self.db.add(Wishlist(user_id=user.id))
        self.db.commit()
        self.db.refresh(user)
        token = create_access_token(str(user.id))
        return user, token

    def login(self, *, email: str, password: str) -> tuple[User, str]:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated."
            )
        token = create_access_token(str(user.id))
        return user, token
