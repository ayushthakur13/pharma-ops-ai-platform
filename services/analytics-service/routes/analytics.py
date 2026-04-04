from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas.analytics import DemandTrendsResponse, StockAgingResponse, StorePerformanceResponse
from services.analytics_service import AnalyticsService
from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
ALLOWED_ANALYTICS_ROLES = {"Super Admin", "Manager"}


def _verify_analytics_access(user_info: tuple[User, str]) -> tuple[User, str]:
    user, role_name = user_info
    if role_name not in ALLOWED_ANALYTICS_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires one of: Super Admin, Manager",
        )
    return user, role_name


@router.get("/stock-aging", response_model=StockAgingResponse)
def get_stock_aging(
    store_id: int = Query(..., ge=1),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> StockAgingResponse:
    _verify_analytics_access(get_current_user(token, db))
    service = AnalyticsService(db=db)
    return service.get_stock_aging(store_id=store_id)


@router.get("/demand-trends", response_model=DemandTrendsResponse)
def get_demand_trends(
    store_id: int = Query(..., ge=1),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> DemandTrendsResponse:
    _verify_analytics_access(get_current_user(token, db))
    service = AnalyticsService(db=db)
    return service.get_demand_trends(store_id=store_id)


@router.get("/store-performance", response_model=StorePerformanceResponse)
def get_store_performance(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> StorePerformanceResponse:
    _verify_analytics_access(get_current_user(token, db))
    service = AnalyticsService(db=db)
    return service.get_store_performance()
