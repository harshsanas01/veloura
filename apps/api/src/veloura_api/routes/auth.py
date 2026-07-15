from fastapi import APIRouter

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from veloura_api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    user, token = service.register(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    user, token = service.login(email=payload.email, password=payload.password)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser) -> UserOut:
    return UserOut.model_validate(current_user)
