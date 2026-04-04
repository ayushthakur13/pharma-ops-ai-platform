# 🚀 Centific Pharma Ops AI Platform

A distributed, AI-assisted, microservices-based pharmacy operations platform designed for large-scale healthcare retail chains operating across multiple regions with intermittent connectivity.

---

## Overview

Pharma Ops AI Platform is built to solve real-world operational challenges in pharmacy chains:

- Inventory mismatches and stock-outs  
- Expiry management and compliance risks  
- Lack of real-time visibility across stores  
- Manual and inefficient decision-making  
- Unreliable connectivity in distributed environments  

This system provides a scalable, offline-capable, AI-augmented solution to streamline pharmacy operations and enable data-driven decision-making.

---

## Key Highlights

- Microservices-based architecture  
- Offline-first design with sync capabilities  
- AI-assisted decision support 
- Role-based access control (RBAC)  
- Real-time + eventual consistency model  
- Designed for scalability, reliability, and observability  

---

## System Architecture

### High-Level Components

- **Client (PWA)**  
  Mobile-first responsive interface supporting offline usage  

- **API Gateway**  
  Central entry point for routing, authentication, and request handling  

- **Core Services**
  - Auth Service  
  - Inventory Service  
  - Billing Service  
  - AI Service  
  - Analytics Service  
  - Sync Service  

- **Data Layer**
  - PostgreSQL (centralized)  
  - SQLite (store-level offline DB)  

- **Async Processing**
  - Background workers  
  - Event-driven workflows  

---

## Tech Stack

### Backend
- Python (FastAPI)

### Database
- PostgreSQL (primary)
- SQLite (offline stores)

### Frontend
- Next.js
- TailwindCSS

Runtime requirement (frontend):
- Node.js >= 20.9.0 (required by Next.js 16)

### Frontend Run (Implemented)
- Frontend path: `frontend/`
- Install: `cd frontend && npm install`
- Dev server: `npm run dev`
- Build: `npm run build`
- Expected API Gateway base URL: `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://127.0.0.1:8000`)

### Infrastructure (Planned)
- Redis (caching, queues)
- Message Queue (RabbitMQ)

### AI Layer
- Groq API (LLM inference)
- Rule-based + AI hybrid approach

---

## Core Features

### 1. Authentication & Authorization
- Role-based access control (Super Admin, Manager, Pharmacist, Staff)
- JWT-based authentication
- Demo note: registration currently allows role self-selection (including Super Admin) for assignment simplicity.
- Production note: roles must be assigned by authorized administrators only.

---

### 2. Inventory Management
- Product catalog management  
- Batch-level tracking  
- Expiry monitoring  
- Real-time stock visibility  

---

### 3. Billing & Prescription Flow
- Prescription-linked sales  
- Automatic inventory deduction  
- Transaction logging  

---

### 4. Offline-First Operations
- Local store database (SQLite)  
- Operation queue (write-ahead log)  
- Sync engine for reconciliation  
- Conflict resolution strategy  

---

### 5. AI-Assisted Features

#### Replenishment Recommendations
- Rule-based thresholds + demand trends  
- AI-generated explanations (Groq) as optional layer, not decision maker  

#### Anomaly Detection
- Statistical detection of unusual patterns  
- AI-based contextual insights with deterministic fallback  

#### Conversational Querying
- Natural language → SQL queries  
- Schema-aware prompts  
- Query validation layer  

---

### 6. AI Guardrails (Critical)

- Controlled prompt templates  
- No raw user input sent to LLM  
- Output validation and filtering  
- Confidence scoring  
- Full traceability of AI decisions  
- Input/output/source logging (`rule_based` vs `ai`) for every AI endpoint call

---

### 7. Analytics & BI Dashboards
- Stock aging analysis  
- Demand trends  
- Store performance comparison  
- Operational insights  

---

### 8. Observability & Reliability
- Centralized logging  
- Request tracing  
- Error monitoring  
- Sync failure tracking  

---

### 9. Security & Compliance
- RBAC enforcement  
- Audit logs for all critical actions  
- Data privacy considerations for prescriptions  
- Input validation and API protection  

---

## Service Responsibilities

Auth Service
- Handles users, roles, JWT

Inventory Service
- Owns products, stock, batches
- Enforces JWT authentication on all endpoints

Billing Service
- Owns transactions, prescriptions
- Calls Inventory Service to update stock
- Enforces RBAC for sensitive writes (Pharmacist or Manager)
- Forwards caller JWT token during Inventory deduction calls

AI Service
- Read-only access to analytics data
- Never directly mutates core data

Sync Service
- Stores offline operations in local SQLite queue
- Replays unsynced operations to central service APIs
- Keeps failed operations retryable with replay metadata

API Gateway
- Thin pass-through routing across all service prefixes
- Centralized JWT validation for all non-auth service routes
- Enforces request-size limit and safe header forwarding
- Maps upstream timeout/unavailable errors to 504/503

## Data Ownership

- Inventory data → Inventory Service (source of truth)
- Billing data → Billing Service
- AI does NOT store primary data

## Core Workflows

### Inventory Flow
- Add/update products → track stock → monitor expiry  

### Billing Flow
- Process prescription → generate invoice → update inventory  

### Sync Flow
- Local operations → queue logs → sync to central system  

### AI Flow
- Data aggregation → rule-based analysis → AI explanation  

---

## Database Design (High-Level)

Key entities:

- Users & Roles  
- Stores  
- Products  
- Inventory  
- Batches (expiry tracking)  
- Prescriptions  
- Transactions  
- Audit Logs  

---

## Offline Strategy (Implementation)

- Use SQLite at store level
- Store operations in a local "operations" table
- Each operation has:
  - id
  - type (insert/update)
  - timestamp

- Sync Service:
  - Reads unsynced operations
  - Sends to central API
  - Marks as synced

  ## AI Implementation Constraints

- AI Service must NEVER directly modify database
- All AI outputs must pass validation before use
- Always fallback to rule-based logic

## Design Principles

- **Separation of Concerns**  
  Clear boundaries between services  

- **System First, Features Second**  
  Architecture drives implementation  

- **AI as Augmentation**  
  System remains functional without AI  

- **Offline Resilience**  
  Designed for unreliable connectivity  

- **Explainability Over Black-box AI**  
  Every AI decision is traceable  

---

## Project Structure
```bash
pharma-ops-ai-platform/
│
├── services/
│ ├── auth-service/
│ ├── inventory-service/
│ ├── billing-service/
│ ├── ai-service/
│ ├── analytics-service/
│ └── sync-service/
│
├── api-gateway/
├── frontend/
├── shared/
├── infra/
├── docs/
└── README.md
```


---

## Development Roadmap

### Phase 1
- Architecture design  
- Database schema  

### Phase 2
- Core services implementation  
- API layer  

### Phase 3
- AI features + guardrails  

### Phase 4
- Offline sync simulation  

### Phase 5
- Observability + documentation  

---

## Evaluation Alignment

This project is designed to demonstrate:

- Strong system design thinking  
- Real-world constraint handling  
- Scalable backend architecture  
- Responsible AI integration  
- Clean separation of layers  
- Engineering depth beyond UI  

---

## Disclaimer

This project focuses on system design and engineering depth.  
Not all components are production-complete but are implemented as realistic, extensible modules.

## Current Status

- Phase tracker and backend completion snapshot: [docs/project-phases.md](docs/project-phases.md)
- API contracts: [docs/api-contracts.md](docs/api-contracts.md)

---
