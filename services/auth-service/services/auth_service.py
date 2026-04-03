from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shared.config import settings
from shared.models.audit import AuditLog
from shared.models.user import Role, User

from schemas.auth import LoginRequest, RegisterRequest

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
ALLOWED_ROLES = {"Super Admin", "Manager", "Pharmacist", "Staff"}


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, payload: RegisterRequest) -> tuple[User, str]:
        existing_user = self.db.scalar(select(User).where(User.email == payload.email))
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        normalized_role = self._normalize_role(payload.role)
        role = self._get_or_create_role(normalized_role)

        user = User(
            email=payload.email,
            password_hash=pwd_context.hash(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            role_id=role.id,
            is_active=True,
        )
        self.db.add(user)
        self.db.flush()

        audit = AuditLog(
            entity_type="user",
            entity_id=str(user.id),
            action="create",
            new_value={
                "email": user.email,
                "role": role.name,
            },
            user_id=user.id,
            timestamp=datetime.now(UTC),
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(user)
        return user, role.name

    def login_user(self, payload: LoginRequest) -> tuple[str, int, User, str]:
        user = self.db.scalar(select(User).where(User.email == payload.email))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not pwd_context.verify(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

        role_name = self._get_role_name(user.role_id)
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        expires_at = datetime.now(UTC) + expires_delta

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": role_name,
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        token = jwt.encode(token_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        return token, int(expires_delta.total_seconds()), user, role_name

    def get_current_user(self, token: str) -> tuple[User, str]:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            user_id = int(payload.get("sub", "0"))
        except (JWTError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")

        role_name = self._get_role_name(user.role_id)
        return user, role_name

    def _get_or_create_role(self, role_name: str) -> Role:
        role = self.db.scalar(select(Role).where(func.lower(Role.name) == role_name.lower()))
        if role:
            return role

        role = Role(name=role_name, description=f"{role_name} role")
        self.db.add(role)
        self.db.flush()
        return role

    def _get_role_name(self, role_id: int) -> str:
        role = self.db.get(Role, role_id)
        return role.name if role else "Unknown"

    def _normalize_role(self, raw_role: str) -> str:
        normalized = " ".join(part.capitalize() for part in raw_role.strip().split())
        if normalized not in ALLOWED_ROLES:
            allowed = ", ".join(sorted(ALLOWED_ROLES))
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Role must be one of: {allowed}")
        return normalized
