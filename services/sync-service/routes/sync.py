from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas.sync import (
    SyncOperationCreate,
    SyncOperationRead,
    SyncStatusResponse,
    SyncTriggerResponse,
)
from services.sync_service import SyncService
from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models.user import User

router = APIRouter(prefix="/api/sync", tags=["sync"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
TRIGGER_ALLOWED_ROLES = {"Super Admin", "Manager"}


def _verify_trigger_access(user_info: tuple[User, str]) -> tuple[User, str]:
    user, role_name = user_info
    if role_name not in TRIGGER_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires one of: Super Admin, Manager",
        )
    return user, role_name


@router.post("/operations", response_model=SyncOperationRead, status_code=201)
def create_operation(
    payload: SyncOperationCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> SyncOperationRead:
    user, _ = get_current_user(token, db)
    service = SyncService(db=db)
    return service.create_operation(payload=payload, user_id=user.id)


@router.get("/status/{store_id}", response_model=SyncStatusResponse)
def get_status(
    store_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> SyncStatusResponse:
    get_current_user(token, db)
    service = SyncService(db=db)
    return service.get_status(store_id=store_id)


@router.post("/trigger/{store_id}", response_model=SyncTriggerResponse)
def trigger_sync(
    store_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> SyncTriggerResponse:
    user, _ = _verify_trigger_access(get_current_user(token, db))
    service = SyncService(db=db)
    return service.trigger_sync(store_id=store_id, user_id=user.id, trigger_token=token)
