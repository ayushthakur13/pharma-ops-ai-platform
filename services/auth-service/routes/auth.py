from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas.auth import CurrentUserResponse, LoginRequest, RegisterRequest, TokenResponse, UserRead, UserSummary
from services.auth_service import AuthService
from shared.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    service = AuthService(db)
    user, role_name = service.register_user(payload)
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    token, expires_in, user, role_name = service.login_user(payload)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=UserSummary(id=user.id, email=user.email, role=role_name),
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CurrentUserResponse:
    service = AuthService(db)
    user, role_name = service.get_current_user(token)
    return CurrentUserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=role_name,
        is_active=user.is_active,
    )
