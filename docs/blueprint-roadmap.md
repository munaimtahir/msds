# MSDS Blueprint & Delivery Roadmap

## Vision
Create a resilient municipal services data platform that unifies intake, workflow coordination,
field operations, and reporting across agencies. MSDS emphasizes modularity, compliance, and
operational transparency from day one.

## Guiding Principles
- **Human-centered design:** Build tools that match the daily rituals of municipal staff and field
  inspectors.
- **Data trust:** Maintain lineage, validation, and audit trails to support compliance.
- **Adaptable deployments:** Offer configuration-driven deployments for on-premise, cloud, and
  managed environments such as Replit.
- **Incremental delivery:** Ship thin slices of functionality that unlock value quickly while
  reducing project risk.

## Architecture Blueprint
1. **Presentation Layer**
   - React-based citizen portal for public submissions and status checks.
   - Svelte-based operations console for internal staff triage and oversight.
2. **Service Layer**
   - FastAPI intake service with schema validation, deduplication, and queuing.
   - Temporal workflow orchestrator driving case progression and SLA timers.
   - Reporting adapters (Metabase, dbt models) that expose curated datasets.
3. **Data Layer**
   - PostgreSQL operational store with immutable ledger tables for auditability.
   - Redis cache for accelerating queue lookups and session data.
   - Object storage for attachments, geospatial overlays, and export packages.
4. **Integration Layer**
   - Event-driven connectors (webhooks, SFTP, flat-file) to exchange data with partner systems.
   - API gateway with rate limiting and zero-trust posture for external consumers.

## Delivery Roadmap
| Phase | Timeline | Milestones | Success Criteria |
|-------|----------|------------|------------------|
| **Phase 0 – Foundations** | Weeks 0-2 | Governance kickoff, data inventory, initial schema draft | Stakeholders aligned on scope and success metrics |
| **Phase 1 – Intake & Core Data** | Weeks 3-8 | Intake API, citizen portal MVP, PostgreSQL schema, ETL loaders | 80% of legacy requests migrated, new intake functioning |
| **Phase 2 – Staff Operations** | Weeks 9-14 | Operations console, role-based access control, workflow automation | Average triage time reduced by 40%, SLA tracking live |
| **Phase 3 – Field Toolkit** | Weeks 15-20 | Mobile-first field interface, offline sync, geospatial overlays | 90% sync success rate, inspectors adopt digital updates |
| **Phase 4 – Reporting & Audit** | Weeks 21-24 | Reporting dashboards, audit exports, compliance alerts | Auditors access monthly exports without IT assistance |
| **Phase 5 – Optimization** | Weeks 25-30 | Performance tuning, scale tests, backlog grooming | System supports 5x baseline volume with <2s response time |

## Risk Register (Top 5)
1. **Data Quality Gaps** – Mitigation: embed validation rules in intake flows and create QA
   dashboards.
2. **Change Management Resistance** – Mitigation: schedule staff ride-alongs and training loops in
   each phase.
3. **Integration Complexity** – Mitigation: prioritize partner APIs with pilot agencies and provide
   sandbox credentials early.
4. **Security & Compliance** – Mitigation: adopt CIS benchmarks, implement automated compliance
   scanning, and require least-privilege IAM roles.
5. **Resource Constraints** – Mitigation: cross-train teams, maintain prioritized backlog, and use
   feature flags for staged releases.

## KPIs & Reporting Cadence
- **Service Request Throughput:** Number of requests processed per week.
- **Resolution SLA Adherence:** Percentage of cases closed within defined SLA windows.
- **Data Completeness:** Percentage of required MSDS fields populated across lifecycle stages.
- **Export Reliability:** Success rate of scheduled audit exports and backup jobs.
- **User Satisfaction:** Quarterly survey and qualitative feedback loops with staff and citizens.

## Next Steps
- Finalize acceptance criteria (see `docs/acceptance-tests.md`).
- Complete field mapping exercises with departmental SMEs.
- Stand up development infrastructure following the deployment guides.
- Schedule fortnightly roadmap reviews with product, engineering, and operations leads.
