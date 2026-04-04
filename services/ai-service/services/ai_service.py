from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from statistics import mean, pstdev
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from schemas.ai import (
    AnomalyDetectRequest,
    AnomalyDetectResponse,
    AnomalyItem,
    ConversationalQueryRequest,
    ConversationalQueryResponse,
    ReplenishmentRecommendation,
    ReplenishmentRequest,
    ReplenishmentResponse,
)
from shared.config import settings
from shared.models.audit import AuditLog
from shared.models.billing import Transaction
from shared.models.inventory import Batch, Inventory, Product
from shared.models.store import Store

PROMPT_REPLENISHMENT = (
    "You are a pharmacy operations assistant. Explain the replenishment recommendation in one short sentence. "
    "Do not invent numbers. Use only provided metrics. Keep under 220 characters."
)
PROMPT_ANOMALY = (
    "You are a pharmacy operations analyst. Explain detected billing anomalies in one short sentence. "
    "Do not invent facts. Keep under 220 characters."
)
PROMPT_QUERY = (
    "You are a pharmacy operations insights assistant. Convert structured metrics into a concise natural-language "
    "answer without inventing facts. Keep under 220 characters."
)


class AIService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_replenishment_recommendations(
        self,
        payload: ReplenishmentRequest,
        user_id: int,
    ) -> ReplenishmentResponse:
        self._ensure_store_exists(payload.store_id)
        self._ensure_product_exists(payload.product_id)

        inventory = self.db.scalar(
            select(Inventory).where(
                Inventory.store_id == payload.store_id,
                Inventory.product_id == payload.product_id,
            )
        )

        qty_on_hand = inventory.quantity_on_hand if inventory else 0
        reorder_level = inventory.reorder_level if inventory else 20

        soon_expiry_cutoff = date.today() + timedelta(days=30)
        soon_expiry_qty = self.db.scalar(
            select(func.coalesce(func.sum(Batch.quantity), 0)).where(
                Batch.store_id == payload.store_id,
                Batch.product_id == payload.product_id,
                Batch.expiry_date <= soon_expiry_cutoff,
            )
        )
        soon_expiry_qty = int(soon_expiry_qty or 0)

        recent_from = datetime.now(UTC) - timedelta(days=14)
        daily_counts_rows = self.db.execute(
            select(func.date(Transaction.created_at), func.count(Transaction.id))
            .where(Transaction.store_id == payload.store_id, Transaction.created_at >= recent_from)
            .group_by(func.date(Transaction.created_at))
        ).all()
        daily_counts = [int(row[1]) for row in daily_counts_rows]
        avg_daily_transactions = mean(daily_counts) if daily_counts else 0.0

        demand_pressure = max(1.0, min(3.0, avg_daily_transactions / 20.0 if avg_daily_transactions > 0 else 1.0))
        target_stock = int(max((reorder_level if reorder_level > 0 else 20) * 2 * demand_pressure, 25))

        base_suggested = max(0, target_stock - qty_on_hand)
        adjusted_suggested = max(base_suggested, base_suggested + soon_expiry_qty)

        if adjusted_suggested == 0:
            fallback_reason = (
                f"Stock is healthy at {qty_on_hand} units, above target level {target_stock}; no replenishment needed now."
            )
        else:
            fallback_reason = (
                f"Current stock {qty_on_hand} is below target {target_stock}; suggest ordering {adjusted_suggested} units."
            )
            if soon_expiry_qty > 0:
                fallback_reason += f" Includes {soon_expiry_qty} units expiring within 30 days."

        ai_context = {
            "store_id": payload.store_id,
            "product_id": payload.product_id,
            "quantity_on_hand": qty_on_hand,
            "reorder_level": reorder_level,
            "target_stock": target_stock,
            "suggested_order_quantity": adjusted_suggested,
            "soon_expiry_qty_30d": soon_expiry_qty,
            "avg_daily_transactions_14d": round(avg_daily_transactions, 2),
        }

        reason, source = self._explain_with_ai_or_fallback(
            prompt_template=PROMPT_REPLENISHMENT,
            context=ai_context,
            fallback_text=fallback_reason,
        )

        response = ReplenishmentResponse(
            recommendations=[
                ReplenishmentRecommendation(
                    product_id=payload.product_id,
                    suggested_order_quantity=adjusted_suggested,
                    reason=reason,
                    source=source,
                )
            ]
        )

        self._log_ai_decision(
            action="replenishment_generated",
            user_id=user_id,
            input_payload={
                "store_id": payload.store_id,
                "product_id": payload.product_id,
            },
            output_payload=response.model_dump(mode="json"),
            source=source,
        )
        return response

    def detect_anomalies(self, payload: AnomalyDetectRequest, user_id: int) -> AnomalyDetectResponse:
        self._ensure_store_exists(payload.store_id)

        if payload.date_range.to_date < payload.date_range.from_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_range.to must be greater than or equal to date_range.from",
            )

        start_dt = datetime.combine(payload.date_range.from_date, datetime.min.time())
        end_dt = datetime.combine(payload.date_range.to_date, datetime.max.time())

        rows = self.db.execute(
            select(
                func.date(Transaction.created_at).label("tx_date"),
                func.count(Transaction.id).label("tx_count"),
                func.coalesce(func.sum(Transaction.total_amount), 0).label("tx_revenue"),
            )
            .where(
                Transaction.store_id == payload.store_id,
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            )
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        ).all()

        anomalies: list[AnomalyItem] = []

        counts = [int(row.tx_count) for row in rows]
        revenues = [float(row.tx_revenue) for row in rows]

        if len(counts) >= 2:
            count_mean = mean(counts)
            count_std = pstdev(counts)
            threshold = count_mean + (2 * count_std)

            for row in rows:
                tx_count = int(row.tx_count)
                if tx_count > threshold and tx_count >= max(5, int(count_mean) + 1):
                    confidence = min(0.95, 0.65 + ((tx_count - count_mean) / max(1.0, threshold)))
                    severity = "high" if tx_count > (count_mean + 3 * max(count_std, 1)) else "medium"
                    anomalies.append(
                        AnomalyItem(
                            type="billing_spike",
                            severity=severity,
                            confidence=round(confidence, 2),
                            explanation=(
                                f"Transactions spiked to {tx_count} on {row.tx_date}; "
                                f"baseline is {count_mean:.1f} per day."
                            ),
                        )
                    )

        if len(revenues) >= 2:
            revenue_mean = mean(revenues)
            revenue_std = pstdev(revenues)
            threshold = revenue_mean + (2 * revenue_std)

            for row in rows:
                tx_revenue = float(row.tx_revenue)
                if tx_revenue > threshold and tx_revenue >= max(1000.0, revenue_mean * 1.2):
                    confidence = min(0.95, 0.6 + ((tx_revenue - revenue_mean) / max(1.0, threshold)))
                    severity = "high" if tx_revenue > (revenue_mean + 3 * max(revenue_std, 1.0)) else "medium"
                    anomalies.append(
                        AnomalyItem(
                            type="revenue_spike",
                            severity=severity,
                            confidence=round(confidence, 2),
                            explanation=(
                                f"Revenue reached {tx_revenue:.2f} on {row.tx_date}; "
                                f"daily average is {revenue_mean:.2f}."
                            ),
                        )
                    )

        fallback_summary = "No anomalies detected for the requested period based on rule thresholds."
        if anomalies:
            fallback_summary = "; ".join(item.explanation for item in anomalies[:2])

        ai_context = {
            "store_id": payload.store_id,
            "date_range": {
                "from": payload.date_range.from_date.isoformat(),
                "to": payload.date_range.to_date.isoformat(),
            },
            "days_with_transactions": len(rows),
            "daily_count_series": counts,
            "daily_revenue_series": [round(x, 2) for x in revenues],
            "detected_anomalies": [item.model_dump() for item in anomalies],
        }

        explanation, source = self._explain_with_ai_or_fallback(
            prompt_template=PROMPT_ANOMALY,
            context=ai_context,
            fallback_text=fallback_summary,
        )

        if anomalies and source == "ai":
            # AI is explanation-only. Replace only text, never anomaly type/severity/confidence decisions.
            anomalies[0].explanation = explanation

        response = AnomalyDetectResponse(
            anomalies=anomalies,
            source=source,
        )

        self._log_ai_decision(
            action="anomaly_detection_generated",
            user_id=user_id,
            input_payload={
                "store_id": payload.store_id,
                "date_range": {
                    "from": payload.date_range.from_date.isoformat(),
                    "to": payload.date_range.to_date.isoformat(),
                },
            },
            output_payload=response.model_dump(mode="json"),
            source=source,
        )
        return response

    def conversational_query(self, payload: ConversationalQueryRequest, user_id: int) -> ConversationalQueryResponse:
        question = payload.question.strip()
        self._validate_query_text(question)
        lowered = question.lower()

        intent = self._classify_query_intent(lowered)
        data: dict[str, Any]
        fallback_answer: str

        if intent == "stock_aging":
            store_id = self._require_store_id(payload.store_id, intent)
            stock_aging = self._compute_stock_aging(store_id)
            data = stock_aging
            fallback_answer = (
                f"Store {store_id} stock aging is: 0-30 days={stock_aging['aging_buckets'][0]['count']}, "
                f"31-60 days={stock_aging['aging_buckets'][1]['count']}, 61+ days={stock_aging['aging_buckets'][2]['count']}."
            )
        elif intent == "demand_trends":
            store_id = self._require_store_id(payload.store_id, intent)
            trends = self._compute_demand_trends(store_id)
            data = trends
            total_days = len(trends["trend"])
            total_transactions = sum(x["transactions"] for x in trends["trend"])
            fallback_answer = (
                f"Store {store_id} has {total_transactions} transactions across {total_days} days in the current trend window."
            )
        elif intent == "store_performance":
            perf = self._compute_store_performance()
            data = perf
            store_count = len(perf["stores"])
            total_revenue = sum(float(x["revenue"]) for x in perf["stores"])
            fallback_answer = (
                f"Store performance covers {store_count} stores with combined revenue {total_revenue:.2f}."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Unsupported query intent. Supported insights are: stock aging, demand trends, store performance."
                ),
            )

        ai_context = {
            "question": question,
            "intent": intent,
            "data": data,
        }

        answer, source = self._explain_with_ai_or_fallback(
            prompt_template=PROMPT_QUERY,
            context=ai_context,
            fallback_text=fallback_answer,
        )

        response = ConversationalQueryResponse(
            answer=answer,
            intent=intent,
            source=source,
            data=data,
        )

        self._log_ai_decision(
            action="conversational_query_generated",
            user_id=user_id,
            input_payload={"question": question, "store_id": payload.store_id},
            output_payload=response.model_dump(mode="json"),
            source=source,
        )
        return response

    def _explain_with_ai_or_fallback(
        self,
        prompt_template: str,
        context: dict[str, Any],
        fallback_text: str,
    ) -> tuple[str, str]:
        # Step 1 is deterministic rules. AI is an optional explanation layer only.
        if not settings.groq_api_key or settings.groq_api_key.startswith("mock_"):
            return fallback_text, "rule_based"

        try:
            content = self._call_groq(prompt_template=prompt_template, context=context)
            validated = self._validate_ai_text(content)
            return validated, "ai"
        except Exception:
            return fallback_text, "rule_based"

    def _call_groq(self, prompt_template: str, context: dict[str, Any]) -> str:
        payload = {
            "model": settings.groq_model,
            "temperature": 0,
            "max_tokens": 120,
            "messages": [
                {"role": "system", "content": prompt_template},
                {"role": "user", "content": f"Context JSON: {context}"},
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=settings.groq_timeout_seconds) as client:
            response = client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        choices = body.get("choices", [])
        if not choices:
            raise ValueError("Groq response missing choices")

        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise ValueError("Groq response content is empty")
        return content

    def _validate_ai_text(self, text: str) -> str:
        cleaned = " ".join(text.strip().split())
        if not cleaned:
            raise ValueError("AI explanation is empty")
        if len(cleaned) > 220:
            raise ValueError("AI explanation exceeded guardrail length")

        banned_patterns = [
            "ignore previous instructions",
            "guaranteed",
            "definitely",
            "always true",
        ]
        normalized = cleaned.lower()
        if any(token in normalized for token in banned_patterns):
            raise ValueError("AI explanation failed safety guardrails")

        return cleaned

    def _validate_query_text(self, question: str) -> None:
        blocked_tokens = [
            "drop table",
            "delete from",
            "truncate",
            "insert into",
            "update ",
            "--",
            "/*",
            "*/",
        ]
        normalized = question.lower()
        if any(token in normalized for token in blocked_tokens):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Query contains unsupported or unsafe pattern",
            )

    def _classify_query_intent(self, question: str) -> str:
        if any(token in question for token in ["stock aging", "aging", "expiry", "expir"]):
            return "stock_aging"
        if any(token in question for token in ["demand", "trend", "transactions over time", "daily transactions"]):
            return "demand_trends"
        if any(token in question for token in ["store performance", "performance", "revenue", "stock out"]):
            return "store_performance"
        return "unsupported"

    def _require_store_id(self, store_id: int | None, intent: str) -> int:
        if store_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"store_id is required for {intent} queries",
            )
        self._ensure_store_exists(store_id)
        return store_id

    def _compute_stock_aging(self, store_id: int) -> dict[str, Any]:
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

        return {
            "store_id": store_id,
            "aging_buckets": [
                {"range": "0-30", "count": bucket_0_30},
                {"range": "31-60", "count": bucket_31_60},
                {"range": "61+", "count": bucket_61_plus},
            ],
        }

    def _compute_demand_trends(self, store_id: int) -> dict[str, Any]:
        rows = self.db.execute(
            select(func.date(Transaction.created_at).label("tx_date"), func.count(Transaction.id).label("tx_count"))
            .where(Transaction.store_id == store_id)
            .group_by(func.date(Transaction.created_at))
            .order_by(func.date(Transaction.created_at))
        ).all()

        return {
            "store_id": store_id,
            "trend": [
                {"date": row.tx_date.isoformat(), "transactions": int(row.tx_count)}
                for row in rows
            ],
        }

    def _compute_store_performance(self) -> dict[str, Any]:
        stores = self.db.scalars(select(Store).order_by(Store.id)).all()
        items: list[dict[str, Any]] = []

        for store in stores:
            total_inventory_rows = int(
                self.db.scalar(select(func.count(Inventory.id)).where(Inventory.store_id == store.id)) or 0
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
            stock_out_rate = round(stock_out_rows / total_inventory_rows, 4) if total_inventory_rows > 0 else 0.0

            transaction_count = int(
                self.db.scalar(select(func.count(Transaction.id)).where(Transaction.store_id == store.id)) or 0
            )
            revenue_raw = self.db.scalar(
                select(func.coalesce(func.sum(Transaction.total_amount), 0)).where(Transaction.store_id == store.id)
            )
            revenue = float(revenue_raw or 0)

            items.append(
                {
                    "store_id": store.id,
                    "stock_out_rate": stock_out_rate,
                    "transaction_count": transaction_count,
                    "revenue": round(revenue, 2),
                }
            )

        return {"stores": items}

    def _log_ai_decision(
        self,
        action: str,
        user_id: int,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
        source: str,
    ) -> None:
        log = AuditLog(
            entity_type="ai_service",
            entity_id=str(input_payload.get("store_id", "unknown")),
            action=action,
            user_id=user_id,
            new_value={
                "input": input_payload,
                "output": output_payload,
                "source": source,
            },
            timestamp=datetime.now(UTC),
        )
        self.db.add(log)
        self.db.commit()

    def _ensure_store_exists(self, store_id: int) -> None:
        store = self.db.get(Store, store_id)
        if not store:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

    def _ensure_product_exists(self, product_id: int) -> None:
        product = self.db.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
