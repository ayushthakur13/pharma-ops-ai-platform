from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas.ai import (
    AnomalyDetectRequest,
    AnomalyDetectResponse,
    ConversationalQueryRequest,
    ConversationalQueryResponse,
    ReplenishmentRequest,
    ReplenishmentResponse,
)
from services.ai_service import AIService
from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models.user import User

router = APIRouter(prefix="/api/ai", tags=["ai"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
AI_ALLOWED_ROLES = {"Super Admin", "Manager", "Pharmacist"}


def _verify_ai_access(user_info: tuple[User, str]) -> tuple[User, str]:
    user, role_name = user_info
    if role_name not in AI_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires one of: Super Admin, Manager, Pharmacist",
        )
    return user, role_name


@router.post("/recommendations/replenishment", response_model=ReplenishmentResponse)
def get_replenishment_recommendations(
    payload: ReplenishmentRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ReplenishmentResponse:
    user, _ = _verify_ai_access(get_current_user(token, db))
    service = AIService(db=db)
    return service.get_replenishment_recommendations(payload=payload, user_id=user.id)


@router.post("/anomalies/detect", response_model=AnomalyDetectResponse)
def detect_anomalies(
    payload: AnomalyDetectRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AnomalyDetectResponse:
    user, _ = _verify_ai_access(get_current_user(token, db))
    service = AIService(db=db)
    return service.detect_anomalies(payload=payload, user_id=user.id)


@router.post("/query", response_model=ConversationalQueryResponse)
def conversational_query(
    payload: ConversationalQueryRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ConversationalQueryResponse:
    user, _ = _verify_ai_access(get_current_user(token, db))
    service = AIService(db=db)
    return service.conversational_query(payload=payload, user_id=user.id)
