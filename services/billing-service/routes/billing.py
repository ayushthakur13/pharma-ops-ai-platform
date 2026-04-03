from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas.billing import (
    InventoryDeductionSummary,
    PrescriptionCreate,
    PrescriptionRead,
    TransactionCreate,
    TransactionCreateResponse,
    TransactionRead,
)
from services.billing_service import BillingService
from shared.config import settings
from shared.database import get_db

router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_billing_service(db: Session) -> BillingService:
    inventory_base_url = settings.inventory_service_url
    timeout = settings.inventory_service_timeout_seconds
    return BillingService(db=db, inventory_base_url=inventory_base_url, inventory_timeout_seconds=timeout)


@router.post("/prescriptions", response_model=PrescriptionRead, status_code=201)
def create_prescription(payload: PrescriptionCreate, db: Session = Depends(get_db)) -> PrescriptionRead:
    service = get_billing_service(db)
    return service.create_prescription(payload)


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionRead)
def get_prescription(prescription_id: int, db: Session = Depends(get_db)) -> PrescriptionRead:
    service = get_billing_service(db)
    return service.get_prescription(prescription_id)


@router.post("/transactions", response_model=TransactionCreateResponse, status_code=201)
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)) -> TransactionCreateResponse:
    service = get_billing_service(db)
    transaction, remaining_quantity = service.create_transaction(payload)
    return TransactionCreateResponse(
        id=transaction.id,
        prescription_id=transaction.prescription_id,
        store_id=transaction.store_id,
        created_by_user_id=transaction.created_by_user_id,
        payment_method=transaction.payment_method,
        total_amount=transaction.total_amount,
        inventory_deduction=InventoryDeductionSummary(success=True, remaining_quantity=remaining_quantity),
        created_at=transaction.created_at,
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)) -> TransactionRead:
    service = get_billing_service(db)
    return service.get_transaction(transaction_id)
