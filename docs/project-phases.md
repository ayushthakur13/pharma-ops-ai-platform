# Centific Pharma Ops AI Platform - Complete Project Phases

This document defines the remaining implementation phases from the current state to project completion.

Current state at the time of this document:
- Core PostgreSQL schema is implemented and migrated.
- Shared SQLAlchemy models and config are implemented.
- Inventory Service minimal endpoints are implemented and smoke-tested.
- Local PostgreSQL is running and reachable.

## Delivery Rules (Apply to all phases)

- Keep services logically separate by responsibility.
- Use a single PostgreSQL database with logical ownership boundaries.
- Service-to-service communication must happen through APIs only.
- Do not let AI write directly to core tables.
- Implement minimal working functionality first, then expand.
- Keep migrations simple using Alembic.
- Maintain zero-cost local-first development setup.
- Enforce RBAC at service endpoints that require role control (Auth, Billing, Analytics, admin actions in Inventory).
- Include explicit failure handling for every service (validation errors, upstream failures, retries/timeouts where applicable).

## Phase 0 - Foundation and Schema (Completed)

Objectives:
- Create repository structure for all services and shared modules.
- Define shared database configuration and base models.
- Implement initial Alembic migration with 9 core tables.

Status:
- Completed.

Acceptance criteria:
- Alembic at head.
- Tables exist: users, roles, stores, products, inventory, batches, prescriptions, transactions, audit_logs.

## Phase 1 - Service Bootstrap (Completed)

Objectives:
- Prepare service folder scaffolding.
- Ensure shared imports and startup paths are stable.

Status:
- Completed baseline for inventory and global structure.

Acceptance criteria:
- Service startup works.
- Shared modules resolve correctly.

## Phase 1.5 - API Contracts (Must be finalized before remaining services)

Objectives:
- Freeze request and response contracts for all remaining services.
- Validate non-overlapping boundaries.

Deliverables:
- Auth Service contracts.
- Billing Service contracts.
- AI Service contracts.
- Sync Service contracts.
- Analytics Service contracts.
- API Gateway pass-through routing map.

Acceptance criteria:
- Each endpoint has a clear schema.
- Ownership is unambiguous by service.

## Phase 2 - Inventory Service (Completed, baseline)

Objectives:
- Product creation.
- Stock add, stock update, and retrieval by store.
- Batch creation.
- Internal stock deduction endpoint.

Status:
- Completed minimal baseline.

Next expansion tasks (later):
- Add explicit stock update endpoint (PUT /api/inventory/stock/{inventory_id}) with audit logging.
- Expiry intelligence queries.
- Better error codes and pagination.
- Add structured failure handling for invalid payloads, missing entities, and DB constraint violations.

## Phase 3 - Auth Service (Next)

Objectives:
- Implement user registration.
- Implement login with JWT generation.
- Implement current user endpoint.

Minimal endpoints:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

Data ownership:
- Owns users and roles logic.

Acceptance criteria:
- Password hashing works.
- JWT payload generated and validated.
- Protected route returns current user context.
- Role checks are enforced for role-restricted operations.

## Phase 4 - Billing Service

Objectives:
- Create prescriptions.
- Create transactions.
- Deduct stock by calling Inventory Service API.

Minimal endpoints:
- POST /api/billing/prescriptions
- GET /api/billing/prescriptions/{id}
- POST /api/billing/transactions
- GET /api/billing/transactions/{id}

Data ownership:
- Owns prescriptions and transactions.

Acceptance criteria:
- Billing transaction fails on insufficient stock.
- Successful billing updates inventory through API call.
- Audit log entries are recorded for key billing actions.
- Service returns clear failure responses for inventory API errors/timeouts and records those failures.

## Phase 5 - AI Service (Read-only, controlled)

Objectives:
- Provide replenishment recommendations.
- Provide anomaly detection insights.

Minimal endpoints:
- POST /api/ai/recommendations/replenishment
- POST /api/ai/anomalies/detect

Constraints:
- No direct writes to core business tables.
- Use prompt templates.
- Validate all outputs.
- Log AI decisions.
- Use mock outputs first, then optional Groq integration.
- On model/provider failure, return deterministic rule-based fallback output.

Acceptance criteria:
- Returns valid structured suggestions.
- Includes fallback rule-based output path.

## Phase 6 - Sync Service (After Billing)

Objectives:
- Simulate offline operation queue in SQLite.
- Replay unsynced operations to central APIs.

Minimal endpoints:
- POST /api/sync/operations
- GET /api/sync/status/{store_id}
- POST /api/sync/trigger/{store_id}

Acceptance criteria:
- Unsynced operations are stored locally.
- Trigger replay calls central APIs and marks successful sync.
- Failed operations remain retryable.
- Sync failures are logged with enough context for replay/debug.

## Phase 7 - Analytics Service

Objectives:
- Build read-only analytical views from core data.

Minimal endpoints:
- GET /api/analytics/stock-aging
- GET /api/analytics/demand-trends
- GET /api/analytics/store-performance

Acceptance criteria:
- Endpoints return valid structured metrics.
- No writes to transactional tables.

## Phase 8 - API Gateway (Pass-through first)

Objectives:
- Route requests to service endpoints.
- Keep gateway thin initially.

Initial behavior:
- Prefix-based pass-through routing.
- No global auth enforcement in first cut.
- Basic request-size limits and safe header forwarding.

Later behavior:
- Add centralized auth checks after Auth Service is stable.
- Add rate limiting/throttling policies.
- Add abuse protection controls (IP/user based protections and route-level guards).

Acceptance criteria:
- All configured service routes forward correctly.
- Error forwarding remains consistent.
- Gateway protection controls are configured and observable in logs/metrics.

## Phase 9 - Frontend (Last)

Objectives:
- Minimal functional UI for end-to-end operations.

Initial screens:
- Login
- Dashboard
- Inventory basic flows
- Billing basic flow
- Analytics summary

Acceptance criteria:
- Mobile-friendly layout works.
- Can execute key operational flow from UI.

## Phase 10 - Hardening and Final Acceptance

Objectives:
- Basic observability and reliability checks.
- Security and audit checks.
- Final walkthrough against assignment criteria.

Checklist:
- Request and error logging.
- Sync failure logging.
- AI decision logging.
- RBAC checks on protected endpoints.
- Basic endpoint tests per service.

Final acceptance criteria:
- Functional requirements satisfied end-to-end.
- Non-functional expectations are documented and addressed at baseline level.
- Repository is runnable locally with clear startup sequence.

## Suggested Execution Sequence from Today

1. Finalize Phase 1.5 API contracts.
2. Implement Auth Service.
3. Implement Billing Service.
4. Implement AI Service (mock first).
5. Implement Sync Service.
6. Implement Analytics Service.
7. Implement API Gateway pass-through.
8. Implement frontend minimal UI.
9. Perform hardening and final acceptance checks.
