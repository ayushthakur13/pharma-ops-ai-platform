from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionCreate(BaseModel):
    patient_id: str = Field(min_length=1, max_length=100)
    store_id: int
    status: str = Field(default="created", min_length=1, max_length=50)


class PrescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: str
    store_id: int
    created_by_user_id: int
    status: str
    created_at: datetime


class TransactionCreate(BaseModel):
    prescription_id: int
    store_id: int
    product_id: int
    quantity: int = Field(gt=0)
    payment_method: str = Field(min_length=1, max_length=50)
    total_amount: Decimal = Field(gt=0)


class InventoryDeductionSummary(BaseModel):
    success: bool
    remaining_quantity: int | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_id: int
    store_id: int
    created_by_user_id: int
    payment_method: str
    total_amount: Decimal
    created_at: datetime


class TransactionCreateResponse(BaseModel):
    id: int
    prescription_id: int
    store_id: int
    created_by_user_id: int
    payment_method: str
    total_amount: Decimal
    inventory_deduction: InventoryDeductionSummary
    created_at: datetime
