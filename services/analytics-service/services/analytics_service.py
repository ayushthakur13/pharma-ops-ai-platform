from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schemas.analytics import (
    AgingBucket,
    DemandTrendPoint,
    DemandTrendsResponse,
    StockAgingResponse,
    StorePerformanceItem,
    StorePerformanceResponse,
)
from shared.models.billing import Transaction
from shared.models.inventory import Batch, Inventory
from shared.models.store import Store


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_stock_aging(self, store_id: int) -> StockAgingResponse:
        self._ensure_store_exists(store_id)

        today = date.today()
        day_30 = today + timedelta(days=30)
        day_60 = today + timedelta(days=60)

        bucket_0_30 = int(
            self.db.scalar(
                select(func.count(Batch.id)).where(
                    Batch.store_id == store_id,
                    Batch.expiry_date >= today,
                    Batch.expiry_date <= day_30,
                )
            )
            or 0
        )
        bucket_31_60 = int(
            self.db.scalar(
                select(func.count(Batch.id)).where(
                    Batch.store_id == store_id,
                    Batch.expiry_date > day_30,
                    Batch.expiry_date <= day_60,
                )
            )
            or 0
        )
        bucket_61_plus = int(
            self.db.scalar(
                select(func.count(Batch.id)).where(
                    Batch.store_id == store_id,
                    Batch.expiry_date > day_60,
                )
            )
            or 0
        )

        return StockAgingResponse(
            store_id=store_id,
            aging_buckets=[
                AgingBucket(range="0-30", count=bucket_0_30),
                AgingBucket(range="31-60", count=bucket_31_60),
                AgingBucket(range="61+", count=bucket_61_plus),
            ],
        )

    def get_demand_trends(self, store_id: int) -> DemandTrendsResponse:
        self._ensure_store_exists(store_id)

        rows = self.db.execute(
            select(func.date(Transaction.created_at).label("tx_date"), func.count(Transaction.id).label("tx_count"))
            .where(Transaction.store_id == store_id)
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        ).all()

        trend = [
            DemandTrendPoint(date=row.tx_date, transactions=int(row.tx_count))
            for row in rows
        ]

        return DemandTrendsResponse(store_id=store_id, trend=trend)

    def get_store_performance(self) -> StorePerformanceResponse:
        stores = self.db.scalars(select(Store).order_by(Store.id)).all()

        items: list[StorePerformanceItem] = []
        for store in stores:
            total_inventory_rows = int(
                self.db.scalar(select(func.count(Inventory.id)).where(Inventory.store_id == store.id))
                or 0
            )
            stock_out_rows = int(
                self.db.scalar(
                    select(func.count(Inventory.id)).where(
                        Inventory.store_id == store.id,
                        Inventory.quantity_on_hand <= Inventory.reorder_level,
                    )
                )
                or 0
            )

            stock_out_rate = (
                round(stock_out_rows / total_inventory_rows, 4) if total_inventory_rows > 0 else 0.0
            )

            transaction_count = int(
                self.db.scalar(select(func.count(Transaction.id)).where(Transaction.store_id == store.id))
                or 0
            )

            revenue_raw = self.db.scalar(
                select(func.coalesce(func.sum(Transaction.total_amount), 0)).where(Transaction.store_id == store.id)
            )
            revenue = revenue_raw if isinstance(revenue_raw, Decimal) else Decimal(str(revenue_raw or 0))

            items.append(
                StorePerformanceItem(
                    store_id=store.id,
                    stock_out_rate=stock_out_rate,
                    transaction_count=transaction_count,
                    revenue=revenue,
                )
            )

        return StorePerformanceResponse(stores=items)

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.db.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
