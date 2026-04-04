from datetime import date

from pydantic import BaseModel, Field


class ReplenishmentRequest(BaseModel):
    store_id: int
    product_id: int


class ReplenishmentRecommendation(BaseModel):
    product_id: int
    suggested_order_quantity: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)
    source: str = Field(pattern="^(rule_based|ai)$")


class ReplenishmentResponse(BaseModel):
    recommendations: list[ReplenishmentRecommendation]


class DateRange(BaseModel):
    from_date: date = Field(alias="from")
    to_date: date = Field(alias="to")


class AnomalyDetectRequest(BaseModel):
    store_id: int
    date_range: DateRange


class AnomalyItem(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    severity: str = Field(pattern="^(low|medium|high)$")
    confidence: float = Field(ge=0, le=1)
    explanation: str = Field(min_length=1, max_length=500)


class AnomalyDetectResponse(BaseModel):
    anomalies: list[AnomalyItem]
    source: str = Field(pattern="^(rule_based|ai)$")


class ConversationalQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=400)
    store_id: int | None = None


class ConversationalQueryResponse(BaseModel):
    answer: str = Field(min_length=1, max_length=500)
    intent: str = Field(min_length=1, max_length=100)
    source: str = Field(pattern="^(rule_based|ai)$")
    data: dict
