from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=50)


class ProductRead(BaseModel):
    id: int
    sku: str
    name: str
    category: str
    price: Decimal
    unit: str

    class Config:
        from_attributes = True


class StockCreate(BaseModel):
    product_id: int
    store_id: int
    quantity: int = Field(gt=0)
    reorder_level: int = Field(default=0, ge=0)


class StockRead(BaseModel):
    id: int
    product_id: int
    store_id: int
    quantity_on_hand: int
    reorder_level: int

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    product_id: int
    store_id: int
    batch_number: str = Field(min_length=1, max_length=100)
    expiry_date: date
    quantity: int = Field(gt=0)


class BatchRead(BaseModel):
    id: int
    product_id: int
    store_id: int
    batch_number: str
    expiry_date: date
    quantity: int

    class Config:
        from_attributes = True


class DeductStockRequest(BaseModel):
    product_id: int
    store_id: int
    quantity: int = Field(gt=0)


class DeductStockResponse(BaseModel):
    success: bool
    message: str
    remaining_quantity: int | None = None
