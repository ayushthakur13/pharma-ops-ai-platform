# Centific Pharma Ops AI Platform - API Contracts (Phase 1.5)

This document is the contract baseline for service implementation after Inventory Service.

Scope:
- Defines endpoint contracts for Auth, Billing, AI, Sync, Analytics, and API Gateway.
- Captures ownership boundaries and cross-service dependencies.
- Defines request and response shape for minimal implementation.

Out of scope for this phase:
- Full OpenAPI generation per service.
- Frontend contracts.

## 1. Global API Rules

Base path:
- All endpoints are exposed under /api.

Content type:
- Request: application/json
- Response: application/json

Error envelope (standard):
- error: machine-readable error code
- message: human-readable summary
- details: optional object with field-level context
- request_id: optional correlation id

Example error response:
{
  "error": "validation_error",
  "message": "Invalid input payload",
  "details": {
    "field": "email",
    "reason": "invalid_format"
  },
  "request_id": "req_123"
}

HTTP code conventions:
- 200: successful read/action
- 201: successful resource creation
- 400: invalid request shape/value
- 401: missing/invalid auth token
- 403: authenticated but forbidden by RBAC
- 404: target resource not found
- 409: conflict (duplicate/constraint violation)
- 422: semantic validation failure
- 500: internal service error
- 502/503/504: upstream dependency failure

Service health conventions:
- Each service exposes `GET /health` outside `/api` for liveness checks.
- Response shape:
{
  "status": "ok",
  "service": "<service-name>"
}

RBAC conventions:
- Super Admin: platform-level privileged operations
- Manager: store/regional operational control
- Pharmacist: prescription and billing operations
- Staff: limited operational read/write actions

## 2. Data Ownership and Boundaries

Auth Service owns:
- users
- roles

Inventory Service owns:
- products
- inventory
- batches

Billing Service owns:
- prescriptions
- transactions

AI Service owns:
- no primary transactional table ownership
- read-only insights

Shared table usage:
- stores: read usage across services
- audit_logs: append by services for critical actions

Cross-service rule:
- No direct DB query into another service domain.
- Use API call for cross-domain behavior.

## 3. Auth Service Contracts

Service prefix:
- /api/auth

### 3.1 POST /api/auth/register
Purpose:
- Create a user account.

Auth:
- Minimal phase: open for bootstrap
- Expanded phase: Super Admin only

Request body:
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "Staff"
}

Response 201:
{
  "id": 10,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "Staff",
  "is_active": true,
  "created_at": "2026-04-04T12:00:00Z"
}

Failures:
- 409 if email already exists
- 422 on weak/invalid password

### 3.2 POST /api/auth/login
Purpose:
- Authenticate user and issue JWT.

Request body:
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}

Response 200:
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 10,
    "email": "user@example.com",
    "role": "Staff"
  }
}

Failures:
- 401 for invalid credentials
- 403 for inactive account

### 3.3 GET /api/auth/me
Purpose:
- Return identity from JWT context.

Auth:
- Required

Response 200:
{
  "id": 10,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "Staff",
  "is_active": true
}

Failures:
- 401 invalid/missing token

### 3.4 GET /health
Purpose:
- Service liveness probe.

Response 200:
{
  "status": "ok",
  "service": "auth-service"
}

## 4. Billing Service Contracts

Service prefix:
- /api/billing

Dependency:
- Calls Inventory Service /api/inventory/deduct
- Forwards caller JWT to Inventory Service as Bearer token.

### 4.1 POST /api/billing/prescriptions
Purpose:
- Create a prescription record.

Auth:
- Pharmacist or Manager

Request body:
{
  "patient_id": "PAT-001",
  "store_id": 1,
  "status": "created"
}

Response 201:
{
  "id": 50,
  "patient_id": "PAT-001",
  "store_id": 1,
  "created_by_user_id": 10,
  "status": "created",
  "created_at": "2026-04-04T12:10:00Z"
}

### 4.2 GET /api/billing/prescriptions/{id}
Response 200:
{
  "id": 50,
  "patient_id": "PAT-001",
  "store_id": 1,
  "created_by_user_id": 10,
  "status": "created",
  "created_at": "2026-04-04T12:10:00Z"
}

Failures:
- 404 if prescription not found

### 4.3 POST /api/billing/transactions
Purpose:
- Create transaction and deduct stock via Inventory API.

Auth:
- Pharmacist or Manager

Request body:
{
  "prescription_id": 50,
  "store_id": 1,
  "product_id": 1,
  "quantity": 2,
  "payment_method": "cash",
  "total_amount": 99.98
}

Response 201:
{
  "id": 80,
  "prescription_id": 50,
  "store_id": 1,
  "created_by_user_id": 10,
  "payment_method": "cash",
  "total_amount": 99.98,
  "inventory_deduction": {
    "success": true,
    "remaining_quantity": 88
  },
  "created_at": "2026-04-04T12:20:00Z"
}

Failure handling:
- If inventory deduct fails, return 409 or 502 and do not create transaction row.
- On upstream timeout, return 504 with dependency context.
- On upstream unavailable, return 503 with dependency context.

### 4.4 GET /api/billing/transactions/{id}
Response 200:
{
  "id": 80,
  "prescription_id": 50,
  "store_id": 1,
  "created_by_user_id": 10,
  "payment_method": "cash",
  "total_amount": 99.98,
  "created_at": "2026-04-04T12:20:00Z"
}

### 4.5 GET /health
Purpose:
- Service liveness probe.

Response 200:
{
  "status": "ok",
  "service": "billing-service"
}

## 5. AI Service Contracts (Read-only)

Service prefix:
- /api/ai

Constraints:
- Never mutates core domain tables.
- Must provide deterministic fallback when model call fails.
- AI model output is explanation-only; decision logic remains rule-based.

Auth:
- JWT required.
- Allowed roles: Super Admin, Manager, Pharmacist.

Guardrails:
- Predefined prompt templates only.
- Output length and safety validation before returning.
- Fallback to rule-based explanation on provider failure or invalid model output.
- Audit logging includes input, output, and source (`rule_based` or `ai`).

### 5.1 POST /api/ai/recommendations/replenishment
Request body:
{
  "store_id": 1,
  "product_id": 1
}

Response 200:
{
  "recommendations": [
    {
      "product_id": 1,
      "suggested_order_quantity": 120,
      "reason": "Stock below reorder threshold",
      "source": "rule_based_or_ai"
    }
  ]
}

### 5.2 POST /api/ai/anomalies/detect
Request body:
{
  "store_id": 1,
  "date_range": {
    "from": "2026-04-01",
    "to": "2026-04-04"
  }
}

Response 200:
{
  "anomalies": [
    {
      "type": "billing_spike",
      "severity": "medium",
      "confidence": 0.82,
      "explanation": "Transaction volume exceeded baseline"
    }
  ],
  "source": "rule_based_or_ai"
}

### 5.3 POST /api/ai/query
Purpose:
- Conversational operational insights using safe intent mapping.

Request body:
{
  "question": "Give me store performance summary",
  "store_id": 1
}

Response 200:
{
  "answer": "Store 1 has a 0% stock out rate, 4 transactions, and $459.91 in revenue.",
  "intent": "store_performance",
  "source": "rule_based_or_ai",
  "data": {
    "stores": [
      {
        "store_id": 1,
        "stock_out_rate": 0.0,
        "transaction_count": 4,
        "revenue": 459.91
      }
    ]
  }
}

Guardrail note:
- No arbitrary SQL execution. Query intent is classified into approved analytics intents only.

## 6. Sync Service Contracts

Service prefix:
- /api/sync

Auth:
- JWT required on all endpoints.
- Trigger endpoint role restriction: Super Admin or Manager.

Persistence:
- Local SQLite operations table used for queue simulation.

### 6.1 POST /api/sync/operations
Request body:
{
  "store_id": 1,
  "operation_type": "create_transaction",
  "entity_id": "80",
  "payload": {
    "prescription_id": 50,
    "total_amount": 99.98
  }
}

Response 201:
{
  "id": 1,
  "store_id": 1,
  "operation_type": "create_transaction",
  "synced_flag": false,
  "created_at": "2026-04-04T12:30:00Z"
}

### 6.2 GET /api/sync/status/{store_id}
Response 200:
{
  "store_id": 1,
  "pending_count": 3,
  "last_sync_at": "2026-04-04T12:00:00Z"
}

### 6.3 POST /api/sync/trigger/{store_id}
Response 200:
{
  "store_id": 1,
  "processed": 3,
  "succeeded": 2,
  "failed": 1,
  "failed_ids": [5]
}

Failure handling:
- Failed sync operations remain unsynced for retry.
- Each failure includes error message and upstream status capture in logs.
- Replay stores retry metadata in local queue (retry_count, upstream_status, last_error).

## 7. Analytics Service Contracts (Read-only)

Service prefix:
- /api/analytics

Auth:
- JWT required on all endpoints.

Liveness endpoint:
- GET /health

### 7.1 GET /api/analytics/stock-aging?store_id=1
Response 200:
{
  "store_id": 1,
  "aging_buckets": [
    {"range": "0-30", "count": 20},
    {"range": "31-60", "count": 8},
    {"range": "61+", "count": 2}
  ]
}

### 7.2 GET /api/analytics/demand-trends?store_id=1
Response 200:
{
  "store_id": 1,
  "trend": [
    {"date": "2026-04-01", "transactions": 32},
    {"date": "2026-04-02", "transactions": 28}
  ]
}

### 7.3 GET /api/analytics/store-performance
Response 200:
{
  "stores": [
    {
      "store_id": 1,
      "stock_out_rate": 0.04,
      "transaction_count": 120,
      "revenue": 45230.50
    }
  ]
}

RBAC:
- Manager or Super Admin for cross-store analytics.

## 8. API Gateway Routing Contract

Gateway prefix:
- /api

Initial behavior:
- Pass-through routing by prefix:
  - /api/auth -> Auth Service
  - /api/inventory -> Inventory Service
  - /api/billing -> Billing Service
  - /api/ai -> AI Service
  - /api/sync -> Sync Service
  - /api/analytics -> Analytics Service

Protection requirements:
- Request size limits enabled.
- Safe header forwarding only.
- Basic abuse protection hooks.
- Rate limiting policy slots configured (enforce later phase).

Failure behavior:
- Upstream timeout -> 504 gateway_timeout
- Upstream unavailable -> 503 service_unavailable
- Preserve downstream error code when pass-through is possible

## 9. Inventory Service Security Contract (Implemented Baseline)

Service prefix:
- /api/inventory

Auth:
- JWT Bearer token required for all Inventory endpoints.

Endpoints covered:
- POST /api/inventory/products
- GET /api/inventory/products/{id}
- POST /api/inventory/stock
- GET /api/inventory/stock/{store_id}
- POST /api/inventory/batches
- POST /api/inventory/deduct

Liveness endpoint:
- GET /health

Failure behavior:
- 401 for missing/invalid token
- Domain errors unchanged (404/409 and business validation responses)

## 10. Contract Completion Checklist

- All endpoints in this document have request and response definitions.
- Service ownership boundaries are explicit.
- Cross-service dependencies are explicit.
- RBAC requirements are specified per sensitive endpoint set.
- Failure handling behavior is defined for each dependency-sensitive service.
