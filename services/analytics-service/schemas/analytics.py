from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class AgingBucket(BaseModel):
    range: str
    count: int = Field(ge=0)


class StockAgingResponse(BaseModel):
    store_id: int
    aging_buckets: list[AgingBucket]


class DemandTrendPoint(BaseModel):
    date: date
    transactions: int = Field(ge=0)


class DemandTrendsResponse(BaseModel):
    store_id: int
    trend: list[DemandTrendPoint]


class StorePerformanceItem(BaseModel):
    store_id: int
    stock_out_rate: float = Field(ge=0, le=1)
    transaction_count: int = Field(ge=0)
    revenue: Decimal = Field(ge=0)


class StorePerformanceResponse(BaseModel):
    stores: list[StorePerformanceItem]
