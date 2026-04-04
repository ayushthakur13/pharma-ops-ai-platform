from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
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
from shared.auth_utils import get_current_user
from shared.config import settings
from shared.database import get_db
from shared.models.user import User

router = APIRouter(prefix="/api/billing", tags=["billing"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_pharmacist_or_manager(user_info: tuple[User, str]) -> tuple[User, str]:
    """Verify user has Pharmacist or Manager role."""
    user, role_name = user_info
    if role_name not in ["Pharmacist", "Manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires Pharmacist or Manager role"
        )
    return user, role_name


def get_billing_service(db: Session) -> BillingService:
    inventory_base_url = settings.inventory_service_url
    timeout = settings.inventory_service_timeout_seconds
    return BillingService(db=db, inventory_base_url=inventory_base_url, inventory_timeout_seconds=timeout)


@router.post("/prescriptions", response_model=PrescriptionRead, status_code=201)
def create_prescription(
    payload: PrescriptionCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PrescriptionRead:
    user, role = verify_pharmacist_or_manager(get_current_user(token, db))
    service = get_billing_service(db)
    return service.create_prescription(payload, user_id=user.id)


@router.get("/prescriptions/{prescription_id}", response_model=PrescriptionRead)
def get_prescription(
    prescription_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> PrescriptionRead:
    get_current_user(token, db)  # Validate auth
    service = get_billing_service(db)
    return service.get_prescription(prescription_id)


@router.post("/transactions", response_model=TransactionCreateResponse, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> TransactionCreateResponse:
    user, role = verify_pharmacist_or_manager(get_current_user(token, db))
    service = get_billing_service(db)
    transaction, remaining_quantity = service.create_transaction(payload, user_id=user.id, auth_token=token)
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
def get_transaction(
    transaction_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> TransactionRead:
    get_current_user(token, db)  # Validate auth
    service = get_billing_service(db)
    return service.get_transaction(transaction_id)
