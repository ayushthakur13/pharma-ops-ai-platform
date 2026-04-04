from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from schemas.sync import SyncOperationCreate, SyncOperationRead, SyncStatusResponse, SyncTriggerResponse
from shared.config import settings
from shared.models.audit import AuditLog
from shared.models.store import Store


class SyncService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sqlite_path = self._resolve_sqlite_path(settings.sync_sqlite_path)
        self.replay_timeout_seconds = settings.sync_replay_timeout_seconds
        self._ensure_sqlite_table()

    def create_operation(self, payload: SyncOperationCreate, user_id: int) -> SyncOperationRead:
        self._ensure_store_exists(payload.store_id)

        created_at = datetime.now(UTC)
        conn = self._sqlite_connect()
        try:
            cursor = conn.execute(
                """
                INSERT INTO sync_operations (
                    store_id,
                    operation_type,
                    entity_id,
                    payload,
                    synced_flag,
                    created_at,
                    retry_count
                ) VALUES (?, ?, ?, ?, 0, ?, 0)
                """,
                (
                    payload.store_id,
                    payload.operation_type,
                    payload.entity_id,
                    json.dumps(payload.payload),
                    created_at.isoformat(),
                ),
            )
            conn.commit()
            operation_id = int(cursor.lastrowid)
        finally:
            conn.close()

        self._log_audit(
            action="sync_operation_queued",
            user_id=user_id,
            entity_id=str(operation_id),
            new_value={
                "store_id": payload.store_id,
                "operation_type": payload.operation_type,
                "entity_id": payload.entity_id,
                "payload": payload.payload,
                "source": "offline_queue",
            },
        )

        return SyncOperationRead(
            id=operation_id,
            store_id=payload.store_id,
            operation_type=payload.operation_type,
            synced_flag=False,
            created_at=created_at,
        )

    def get_status(self, store_id: int) -> SyncStatusResponse:
        self._ensure_store_exists(store_id)

        conn = self._sqlite_connect()
        try:
            pending_count = int(
                conn.execute(
                    "SELECT COUNT(*) AS c FROM sync_operations WHERE store_id = ? AND synced_flag = 0",
                    (store_id,),
                ).fetchone()["c"]
            )
            last_sync_raw = conn.execute(
                "SELECT MAX(synced_at) AS last_sync_at FROM sync_operations WHERE store_id = ? AND synced_flag = 1",
                (store_id,),
            ).fetchone()["last_sync_at"]
        finally:
            conn.close()

        last_sync_at = datetime.fromisoformat(last_sync_raw) if last_sync_raw else None
        return SyncStatusResponse(store_id=store_id, pending_count=pending_count, last_sync_at=last_sync_at)

    def trigger_sync(self, store_id: int, user_id: int, trigger_token: str) -> SyncTriggerResponse:
        self._ensure_store_exists(store_id)

        conn = self._sqlite_connect()
        failed_ids: list[int] = []
        processed = 0
        succeeded = 0

        try:
            rows = conn.execute(
                """
                SELECT id, operation_type, entity_id, payload, retry_count
                FROM sync_operations
                WHERE store_id = ? AND synced_flag = 0
                ORDER BY id ASC
                """,
                (store_id,),
            ).fetchall()

            for row in rows:
                processed += 1
                operation_id = int(row["id"])
                operation_type = str(row["operation_type"])
                payload = self._parse_payload(row["payload"])
                attempt_token = trigger_token

                try:
                    self._replay_operation(operation_type=operation_type, payload=payload, token=attempt_token)
                    conn.execute(
                        """
                        UPDATE sync_operations
                        SET synced_flag = 1,
                            synced_at = ?,
                            last_error = NULL,
                            upstream_status = NULL
                        WHERE id = ?
                        """,
                        (datetime.now(UTC).isoformat(), operation_id),
                    )
                    succeeded += 1
                except HTTPException as exc:
                    failed_ids.append(operation_id)
                    conn.execute(
                        """
                        UPDATE sync_operations
                        SET retry_count = retry_count + 1,
                            last_error = ?,
                            upstream_status = ?
                        WHERE id = ?
                        """,
                        (str(exc.detail), int(exc.status_code), operation_id),
                    )
                    self._log_audit(
                        action="sync_replay_failed",
                        user_id=user_id,
                        entity_id=str(operation_id),
                        new_value={
                            "store_id": store_id,
                            "operation_type": operation_type,
                            "payload": payload,
                            "error": str(exc.detail),
                            "upstream_status": int(exc.status_code),
                        },
                    )
                except Exception as exc:
                    failed_ids.append(operation_id)
                    conn.execute(
                        """
                        UPDATE sync_operations
                        SET retry_count = retry_count + 1,
                            last_error = ?,
                            upstream_status = ?
                        WHERE id = ?
                        """,
                        (str(exc), 500, operation_id),
                    )
                    self._log_audit(
                        action="sync_replay_failed",
                        user_id=user_id,
                        entity_id=str(operation_id),
                        new_value={
                            "store_id": store_id,
                            "operation_type": operation_type,
                            "payload": payload,
                            "error": str(exc),
                            "upstream_status": 500,
                        },
                    )

            conn.commit()
        finally:
            conn.close()

        failed = len(failed_ids)
        self._log_audit(
            action="sync_trigger_completed",
            user_id=user_id,
            entity_id=str(store_id),
            new_value={
                "store_id": store_id,
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed,
                "failed_ids": failed_ids,
            },
        )

        return SyncTriggerResponse(
            store_id=store_id,
            processed=processed,
            succeeded=succeeded,
            failed=failed,
            failed_ids=failed_ids,
        )

    def _replay_operation(self, operation_type: str, payload: dict[str, Any], token: str) -> None:
        method, url = self._resolve_upstream_route(operation_type)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.replay_timeout_seconds) as client:
                response = client.request(method, url, json=payload, headers=headers)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Upstream timeout while replaying {operation_type}",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Upstream unavailable while replaying {operation_type}: {exc}",
            )

        if response.status_code >= 400:
            error_text = response.text.strip() or "upstream request failed"
            raise HTTPException(status_code=response.status_code, detail=error_text)

    def _resolve_upstream_route(self, operation_type: str) -> tuple[str, str]:
        op = operation_type.strip().lower()
        if op == "create_transaction":
            return "POST", f"{settings.billing_service_url.rstrip('/')}/api/billing/transactions"
        if op == "create_prescription":
            return "POST", f"{settings.billing_service_url.rstrip('/')}/api/billing/prescriptions"
        if op == "add_stock":
            return "POST", f"{settings.inventory_service_url.rstrip('/')}/api/inventory/stock"
        if op == "create_product":
            return "POST", f"{settings.inventory_service_url.rstrip('/')}/api/inventory/products"
        if op == "deduct_stock":
            return "POST", f"{settings.inventory_service_url.rstrip('/')}/api/inventory/deduct"

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported operation_type for replay: {operation_type}",
        )

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.db.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _log_audit(self, action: str, user_id: int, entity_id: str, new_value: dict[str, Any]) -> None:
        log = AuditLog(
            entity_type="sync_operation",
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            new_value=new_value,
            timestamp=datetime.now(UTC),
        )
        self.db.add(log)
        self.db.commit()

    def _resolve_sqlite_path(self, configured_path: str) -> Path:
        path = Path(configured_path)
        if path.is_absolute():
            resolved = path
        else:
            repo_root = Path(__file__).resolve().parents[3]
            resolved = repo_root / path
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def _sqlite_connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_sqlite_table(self) -> None:
        conn = self._sqlite_connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store_id INTEGER NOT NULL,
                    operation_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    synced_flag INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    synced_at TEXT NULL,
                    last_error TEXT NULL,
                    upstream_status INTEGER NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _parse_payload(self, raw_payload: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid payload JSON: {exc}")
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="payload must be a JSON object")
        return parsed
