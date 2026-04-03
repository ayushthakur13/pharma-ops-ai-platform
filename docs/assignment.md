# Case Study Assignment: Pharmacy Operations Mobile Web Platform

Design and develop a responsive, mobile-compatible microservices-based web application for a regional pharmacy and healthcare retail chain operating across 260 outlets in three countries. The platform should support secure login and role-based access for super admins, regional managers, pharmacists, and front-counter associates. Core capabilities must include medicine and wellness product inventory management, prescription-linked sales and billing, batch and expiry tracking, real-time stock visibility with automatic replenishment signals, and BI dashboards for store performance, stock aging, and demand trends. The solution should also include agentic AI features such as replenishment recommendations, anomaly detection for unusual dispensing or billing patterns, and conversational querying for operational insights. The application must be built using Python technologies and PostgreSQL, with clear APIs separating UI, services, and data layers. It should be suitable for deployment in a hybrid environment where some stores have intermittent connectivity and must continue limited operations offline before syncing back to the central system. The design must address non-functional requirements including high availability, performance under peak pharmacy rush hours, scalability for seasonal demand spikes, security and privacy for sensitive customer and prescription data, observability, auditability, and reliability. In addition, the solution should include responsible AI-assisted development guardrails, such as safe prompt handling, traceable AI outputs, and controls to prevent hallucinated operational recommendations. The scenario should be realistic for a healthcare-adjacent retail business and demonstrate how the application can improve inventory accuracy, reduce stock-outs, support compliance, and give leadership actionable insights across all locations.

## Expected Deliverables:
A working design and implementation of the pharmacy operations platform, including architecture, APIs, database schema, core workflows, dashboards, AI-assisted features, and documentation demonstrating how the system meets functional and non-functional requirements.

## Evaluation Criteria:
- Responsive mobile-first UI works across phones, tablets, and desktops
- Role-based authentication and authorization are implemented correctly
- Inventory, billing, and stock monitoring workflows function end to end
- PostgreSQL schema and Python services are well structured and maintainable
- APIs are clearly defined between presentation, business, and data layers
- BI dashboards provide meaningful operational and business insights
- Agentic AI features are useful, controlled, and safely integrated
- Offline/intermittent connectivity handling is addressed for store operations
- Security, privacy, audit logging, and compliance considerations are covered
- Performance, scalability, reliability, and observability requirements are explicitly addressed
