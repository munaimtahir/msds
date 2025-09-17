# Acceptance Test Catalogue

This catalogue enumerates high-level acceptance criteria for the MSDS platform. Each scenario maps
to automated regression suites and manual verification activities. IDs follow the format
`<Domain>-<Number>` for traceability with the roadmap and Jira epics.

## Legend
- **Type:** `AUTO` (automated), `MANUAL`, or `HYBRID`.
- **Priority:** `P0` (must pass before release), `P1`, `P2`.
- **Owner:** Responsible team or role.

## Intake & Validation
| ID | Title | Type | Priority | Owner | Description |
|----|-------|------|----------|-------|-------------|
| IN-001 | Citizen request submission | AUTO | P0 | Platform | Submit request with mandatory fields; expect HTTP 201 and persisted record. |
| IN-002 | Duplicate request suppression | AUTO | P1 | Platform | Submit identical payload twice; expect deduplication with reference to original case. |
| IN-003 | Attachment virus scanning | HYBRID | P0 | Security | Upload file with EICAR signature; ensure quarantine workflow triggers and citizen notified. |
| IN-004 | SLA classification | AUTO | P0 | Platform | Intake API assigns SLA clock based on category configuration. |
| IN-005 | Multi-channel ingestion | MANUAL | P1 | Operations | Validate phone hotline transcription and email ingestion create standardized requests. |

## Operations Console
| ID | Title | Type | Priority | Owner | Description |
|----|-------|------|----------|-------|-------------|
| OP-001 | Role-based access control | AUTO | P0 | IAM | Staff with "Supervisor" role can reassign cases; field inspectors cannot. |
| OP-002 | Bulk status updates | AUTO | P1 | Platform | Update 50 cases simultaneously; verify change history contains entries for each case. |
| OP-003 | Offline sync reconciliation | MANUAL | P0 | Field Ops | Inspectors update cases offline; sync resolves conflicts using last-write-wins with audit trail. |
| OP-004 | SLA breach alerts | AUTO | P0 | Platform | Cases nearing SLA deadlines trigger notifications and appear in dashboard filters. |
| OP-005 | Accessibility conformance | MANUAL | P0 | Design | Console screens satisfy WCAG 2.1 AA using automated axe scan plus manual review. |

## Reporting & Audit
| ID | Title | Type | Priority | Owner | Description |
|----|-------|------|----------|-------|-------------|
| RA-001 | Nightly audit export | AUTO | P0 | Data | Export job produces encrypted CSV, uploads to S3, and logs checksum. |
| RA-002 | Immutable ledger verification | AUTO | P0 | Data | Modifying records creates append-only entries; direct updates blocked by database triggers. |
| RA-003 | Data retention policy | HYBRID | P1 | Legal | Records older than retention window archived; purge job emits compliance report. |
| RA-004 | Dashboard accuracy | MANUAL | P1 | Analytics | Compare key metrics (volume, SLA compliance) between dashboard and warehouse queries. |
| RA-005 | Public transparency portal | AUTO | P2 | Platform | Sanitized dataset publishes to open-data endpoint with personal data removed. |

## Integration Layer
| ID | Title | Type | Priority | Owner | Description |
|----|-------|------|----------|-------|-------------|
| INTEGR-001 | Partner webhook delivery | AUTO | P0 | Integrations | Simulate webhook event; partner receives payload with signed headers within 3s. |
| INTEGR-002 | SFTP batch import | HYBRID | P1 | Integrations | Nightly batch ingested; failures alert via PagerDuty. |
| INTEGR-003 | API rate limiting | AUTO | P0 | Security | Exceed rate limits; expect 429 responses and no data loss. |
| INTEGR-004 | Schema evolution | MANUAL | P2 | Data | Rolling deployment preserves backwards compatibility with versioned APIs. |

## Non-Functional
| ID | Title | Type | Priority | Owner | Description |
|----|-------|------|----------|-------|-------------|
| NF-001 | Load test | AUTO | P0 | Performance | Sustained 500 RPS on intake API with <1% error rate. |
| NF-002 | Disaster recovery | MANUAL | P0 | SRE | Trigger infrastructure failover; environment recovers within 60 minutes using documented runbook. |
| NF-003 | Observability | AUTO | P1 | SRE | Service emits traces, structured logs, and metrics with 95% coverage of key paths. |
| NF-004 | Security scanning | AUTO | P0 | Security | CI pipeline runs SAST, dependency scanning, container scanning with zero critical findings. |
| NF-005 | Privacy impact assessment | MANUAL | P1 | Legal | Review data handling flows for compliance with local privacy regulations. |

## Traceability Matrix
| Roadmap Phase | Acceptance Tests |
|---------------|------------------|
| Phase 0 – Foundations | NF-002, NF-004, NF-005 |
| Phase 1 – Intake & Core Data | IN-001, IN-002, IN-004, NF-001 |
| Phase 2 – Staff Operations | OP-001, OP-002, OP-004, NF-003 |
| Phase 3 – Field Toolkit | OP-003, NF-002 |
| Phase 4 – Reporting & Audit | RA-001, RA-002, RA-003, RA-004 |
| Phase 5 – Optimization | INTEGR-001, INTEGR-002, INTEGR-003, NF-001 |

## Execution Cadence
- **Continuous Integration:** All `AUTO` tests run per pull request.
- **Nightly Regression:** Full automated suite plus targeted hybrid smoke tests.
- **Pre-Release:** Manual verification of `P0` and `P1` scenarios with sign-off from owning teams.
- **Post-Release Monitoring:** 48-hour watch window with live dashboards and PagerDuty coverage.
