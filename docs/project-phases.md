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
- Draft contract document: docs/api-contracts.md

Status:
- Completed (v1 baseline finalized and implemented for Auth/Billing/Inventory-aligned behavior).

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

Implemented security update:
- OAuth2 JWT authentication is enforced on Inventory endpoints.

Next expansion tasks (later):
- Add explicit stock update endpoint (PUT /api/inventory/stock/{inventory_id}) with audit logging.
- Expiry intelligence queries.
- Better error codes and pagination.
- Add structured failure handling for invalid payloads, missing entities, and DB constraint violations.

## Phase 3 - Auth Service (Completed, baseline)

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

Status:
- Completed minimal baseline (register, login, me endpoints) with JWT auth and role-aware flows.

## Phase 4 - Billing Service (Completed, baseline)

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

Status:
- Completed minimal baseline (prescriptions + transactions + inventory deduction integration + strict failure handling + RBAC enforcement on write endpoints).

## Phase 5 - AI Service (Read-only, controlled) (Completed, baseline)

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
- Use Groq API integration as explanation layer and natural language insight.
- On model/provider failure, return deterministic rule-based fallback output.

Acceptance criteria:
- Returns valid structured suggestions.
- Includes fallback rule-based output path.

Status:
- Completed baseline (rule-based recommendations and anomaly detection implemented).
- Groq integrated as explanation-only layer with guardrails and deterministic fallback.
- AI input/output/source logging implemented in audit_logs.
- Conversational query endpoint implemented with safe intent mapping and guardrails.

## Phase 6 - Sync Service (After Billing) (Completed, baseline)

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

Status:
- Completed baseline (SQLite offline queue + replay trigger + status endpoint).
- Successful replay marks operations as synced with synced_at timestamp.
- Failure path preserves unsynced operations with retry_count, upstream_status, and last_error.
- Replay failures are audit logged with payload and error context.

## Phase 7 - Analytics Service (Completed, baseline)

Objectives:
- Build read-only analytical views from core data.

Minimal endpoints:
- GET /api/analytics/stock-aging
- GET /api/analytics/demand-trends
- GET /api/analytics/store-performance

Acceptance criteria:
- Endpoints return valid structured metrics.
- No writes to transactional tables.

Status:
- Completed baseline with read-only analytics endpoints.
- Implemented: stock-aging, demand-trends, and store-performance.
- RBAC enforced for Manager and Super Admin roles.

## Phase 8 - API Gateway (Pass-through first) (Completed, baseline)

Objectives:
- Route requests to service endpoints.
- Keep gateway thin initially.

Initial behavior:
- Prefix-based pass-through routing.
- Centralized JWT auth enforcement for all non-auth service prefixes.
- Basic request-size limits and safe header forwarding.

Later behavior:
- Add rate limiting/throttling policies.
- Add abuse protection controls (IP/user based protections and route-level guards).

Acceptance criteria:
- All configured service routes forward correctly.
- Error forwarding remains consistent.
- Gateway protection controls are configured and observable in logs/metrics.

Status:
- Completed baseline with thin prefix-based pass-through routing.
- Implemented service mappings for auth, inventory, billing, ai, sync, and analytics prefixes.
- Implemented centralized token validation at gateway by verifying Bearer JWT via Auth Service for non-auth routes.
- Implemented request-size limit enforcement and safe request/response header forwarding.
- Implemented upstream failure mapping (504 gateway_timeout, 503 service_unavailable) while preserving downstream status codes when available.

## Phase 9 - Frontend (Last) (Completed, baseline)

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

Status:
- Completed baseline Next.js App Router frontend with mobile-first responsive layouts.
- Implemented login + JWT auth flow via API Gateway (`/api/auth/login`, `/api/auth/me`).
- Implemented role-based protected routes and role-aware navigation/actions.
- Implemented pages: dashboard, inventory, billing, analytics, and AI insights using gateway APIs only.
- Added offline indicator and lightweight offline queue simulation for write actions on network failure.
- Demo note: self-registration supports role selection for assignment demonstration.
- Production note: role assignment must be admin-controlled and removed from open registration.

## Phase 10 - Hardening and Final Acceptance (Completed, backend baseline)

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

Status:
- Completed backend baseline hardening implementation.
- Request and error logging middleware implemented across all backend services and API Gateway.
- `/metrics` endpoint added across all backend services and API Gateway for runtime request/error visibility.
- API Gateway rate limiting enabled with configurable request/window controls.
- Backend acceptance tests added and passing (`tests/test_backend_phase10.py`).

Notes:
- Phase 10 completion here reflects backend hardening baseline; frontend delivery is tracked in Phase 9.

## Implementation Completion Snapshot

Included in the implemented baseline:
- Database schema and shared backend foundation
- Auth, Inventory, Billing, AI, Sync, Analytics, and API Gateway services
- Shared request/error logging and runtime metrics on every backend service
- Gateway centralized JWT validation for non-auth routes and rate limiting controls
- AI guardrails, audit logging, and deterministic fallback behavior
- SQLite offline sync queue with replay and retry metadata
- Backend verification tests for health, metrics, auth rejection, and gateway rate limiting
- Frontend role-based routes and end-to-end operational flows through API Gateway

Alignment verdict:
- Overall implementation is aligned with the assignment requirements at submission baseline level.
- The remaining gap is production-grade observability maturity beyond the current baseline.

## Suggested Execution Sequence

1. Execute full end-to-end walkthrough including UI + backend flows.
2. Expand observability from baseline metrics/logging to production-grade traces and dashboards if targeting production readiness.
