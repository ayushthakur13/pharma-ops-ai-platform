from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from schemas.inventory import (
    BatchCreate,
    BatchRead,
    DeductStockRequest,
    DeductStockResponse,
    ProductCreate,
    ProductRead,
    StockCreate,
    StockRead,
)
from services.inventory_service import InventoryService
from shared.auth_utils import get_current_user
from shared.database import get_db
from shared.models.user import User

router = APIRouter(prefix="/api/inventory", tags=["inventory"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(
    payload: ProductCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ProductRead:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    return service.create_product(payload)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ProductRead:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    return service.get_product(product_id)


@router.post("/stock", response_model=StockRead, status_code=201)
def add_stock(
    payload: StockCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> StockRead:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    return service.add_stock(payload)


@router.get("/stock/{store_id}", response_model=list[StockRead])
def get_stock_by_store(
    store_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> list[StockRead]:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    return service.get_stock_by_store(store_id)


@router.post("/batches", response_model=BatchRead, status_code=201)
def create_batch(
    payload: BatchCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> BatchRead:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    return service.create_batch(payload)


@router.post("/deduct", response_model=DeductStockResponse)
def deduct_stock(
    payload: DeductStockRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> DeductStockResponse:
    get_current_user(token, db)  # Validate auth
    service = InventoryService(db)
    success, message, remaining = service.deduct_stock(payload)
    return DeductStockResponse(success=success, message=message, remaining_quantity=remaining)
