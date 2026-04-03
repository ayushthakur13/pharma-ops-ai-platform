from fastapi import APIRouter, Depends
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
from shared.database import get_db

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.post("/products", response_model=ProductRead, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    service = InventoryService(db)
    return service.create_product(payload)


@router.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    service = InventoryService(db)
    return service.get_product(product_id)


@router.post("/stock", response_model=StockRead, status_code=201)
def add_stock(payload: StockCreate, db: Session = Depends(get_db)) -> StockRead:
    service = InventoryService(db)
    return service.add_stock(payload)


@router.get("/stock/{store_id}", response_model=list[StockRead])
def get_stock_by_store(store_id: int, db: Session = Depends(get_db)) -> list[StockRead]:
    service = InventoryService(db)
    return service.get_stock_by_store(store_id)


@router.post("/batches", response_model=BatchRead, status_code=201)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db)) -> BatchRead:
    service = InventoryService(db)
    return service.create_batch(payload)


@router.post("/deduct", response_model=DeductStockResponse)
def deduct_stock(payload: DeductStockRequest, db: Session = Depends(get_db)) -> DeductStockResponse:
    service = InventoryService(db)
    success, message, remaining = service.deduct_stock(payload)
    return DeductStockResponse(success=success, message=message, remaining_quantity=remaining)
