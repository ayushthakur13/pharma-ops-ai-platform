from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SyncOperationCreate(BaseModel):
    store_id: int
    operation_type: str = Field(min_length=1, max_length=100)
    entity_id: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any]


class SyncOperationRead(BaseModel):
    id: int
    store_id: int
    operation_type: str
    synced_flag: bool
    created_at: datetime


class SyncStatusResponse(BaseModel):
    store_id: int
    pending_count: int
    last_sync_at: datetime | None = None


class SyncTriggerResponse(BaseModel):
    store_id: int
    processed: int
    succeeded: int
    failed: int
    failed_ids: list[int]
