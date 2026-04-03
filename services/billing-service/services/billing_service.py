from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from shared.models.audit import AuditLog
from shared.models.billing import Prescription, Transaction
from shared.models.store import Store
from shared.models.user import User

from schemas.billing import PrescriptionCreate, TransactionCreate


class BillingService:
    def __init__(self, db: Session, inventory_base_url: str, inventory_timeout_seconds: float) -> None:
        self.db = db
        self.inventory_base_url = inventory_base_url.rstrip("/")
        self.inventory_timeout_seconds = inventory_timeout_seconds

    def create_prescription(self, payload: PrescriptionCreate) -> Prescription:
        self._ensure_store_exists(payload.store_id)
        self._ensure_user_exists(payload.created_by_user_id)

        prescription = Prescription(
            patient_id=payload.patient_id,
            store_id=payload.store_id,
            created_by_user_id=payload.created_by_user_id,
            status=payload.status,
        )
        self.db.add(prescription)
        self.db.flush()

        self._log_audit(
            entity_type="prescription",
            entity_id=str(prescription.id),
            action="create",
            user_id=payload.created_by_user_id,
            new_value={
                "patient_id": payload.patient_id,
                "store_id": payload.store_id,
                "status": payload.status,
            },
        )

        self.db.commit()
        self.db.refresh(prescription)
        return prescription

    def get_prescription(self, prescription_id: int) -> Prescription:
        prescription = self.db.get(Prescription, prescription_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
        return prescription

    def create_transaction(self, payload: TransactionCreate) -> tuple[Transaction, int | None]:
        prescription = self.db.get(Prescription, payload.prescription_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")

        if prescription.store_id != payload.store_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Prescription store mismatch")

        self._ensure_user_exists(payload.created_by_user_id)

        deduction_result = self._deduct_inventory_or_fail(
            product_id=payload.product_id,
            store_id=payload.store_id,
            quantity=payload.quantity,
            created_by_user_id=payload.created_by_user_id,
            prescription_id=payload.prescription_id,
        )

        transaction = Transaction(
            prescription_id=payload.prescription_id,
            store_id=payload.store_id,
            total_amount=payload.total_amount,
            payment_method=payload.payment_method,
            created_by_user_id=payload.created_by_user_id,
        )
        self.db.add(transaction)
        self.db.flush()

        self._log_audit(
            entity_type="transaction",
            entity_id=str(transaction.id),
            action="create",
            user_id=payload.created_by_user_id,
            new_value={
                "prescription_id": payload.prescription_id,
                "store_id": payload.store_id,
                "payment_method": payload.payment_method,
                "total_amount": float(payload.total_amount),
                "inventory_remaining": deduction_result.get("remaining_quantity"),
            },
        )

        self.db.commit()
        self.db.refresh(transaction)
        return transaction, deduction_result.get("remaining_quantity")

    def get_transaction(self, transaction_id: int) -> Transaction:
        transaction = self.db.get(Transaction, transaction_id)
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return transaction

    def _deduct_inventory_or_fail(
        self,
        product_id: int,
        store_id: int,
        quantity: int,
        created_by_user_id: int,
        prescription_id: int,
    ) -> dict[str, Any]:
        url = f"{self.inventory_base_url}/api/inventory/deduct"
        payload = {
            "product_id": product_id,
            "store_id": store_id,
            "quantity": quantity,
        }

        try:
            with httpx.Client(timeout=self.inventory_timeout_seconds) as client:
                response = client.post(url, json=payload)
        except httpx.TimeoutException:
            self._log_audit(
                entity_type="transaction",
                entity_id=str(prescription_id),
                action="inventory_deduct_timeout",
                user_id=created_by_user_id,
                new_value={"url": url, "payload": payload},
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Inventory service timeout during stock deduction",
            )
        except httpx.RequestError as exc:
            self._log_audit(
                entity_type="transaction",
                entity_id=str(prescription_id),
                action="inventory_deduct_unavailable",
                user_id=created_by_user_id,
                new_value={"url": url, "payload": payload, "error": str(exc)},
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Inventory service unavailable during stock deduction",
            )

        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code >= 500:
            self._log_audit(
                entity_type="transaction",
                entity_id=str(prescription_id),
                action="inventory_deduct_upstream_error",
                user_id=created_by_user_id,
                new_value={"status_code": response.status_code, "body": body},
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Inventory service failed during stock deduction",
            )

        if response.status_code >= 400:
            self._log_audit(
                entity_type="transaction",
                entity_id=str(prescription_id),
                action="inventory_deduct_request_failed",
                user_id=created_by_user_id,
                new_value={"status_code": response.status_code, "body": body},
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stock deduction failed",
            )

        success = bool(body.get("success"))
        if not success:
            self._log_audit(
                entity_type="transaction",
                entity_id=str(prescription_id),
                action="inventory_deduct_rejected",
                user_id=created_by_user_id,
                new_value={"body": body},
            )
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=body.get("message", "Stock deduction rejected"),
            )

        return body

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.db.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _ensure_user_exists(self, user_id: int) -> None:
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    def _log_audit(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: int | None,
        new_value: dict[str, Any] | None = None,
    ) -> None:
        audit = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            new_value=new_value,
            timestamp=datetime.now(UTC),
        )
        self.db.add(audit)
