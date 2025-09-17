# MSDS Data Field Mapping

This document defines canonical field names, data types, and lineage for the MSDS operational data
store. Use these mappings when designing APIs, database schemas, ETL processes, and reporting
artifacts.

## Core Entities
### Service Request (`service_requests`)
| Field | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `request_id` | UUID | Generated | Yes | Primary identifier for the request; immutable. |
| `external_reference` | String | Intake | No | ID supplied by partner agencies or legacy systems. |
| `channel` | Enum (`portal`, `phone`, `email`, `field`, `api`) | Intake | Yes | Submission channel. |
| `category` | String | Intake | Yes | Service category selected by citizen or assigned by staff. |
| `subcategory` | String | Intake | No | Optional refinement for analytics. |
| `status` | Enum (`new`, `triaged`, `assigned`, `in_progress`, `waiting_external`, `resolved`, `closed`) | Workflow | Yes | Current lifecycle state. |
| `priority` | Enum (`low`, `medium`, `high`, `critical`) | Workflow | Yes | Derived from SLA rules. |
| `sla_due_at` | Timestamp | Workflow | No | Deadline for SLA compliance. |
| `description` | Text | Intake | Yes | Citizen-provided narrative. |
| `location_lat` | Decimal(9,6) | Geocoder | No | Latitude of service request. |
| `location_lng` | Decimal(9,6) | Geocoder | No | Longitude of service request. |
| `civic_address_id` | UUID | GIS | No | Foreign key to canonical address registry. |
| `created_at` | Timestamp | System | Yes | UTC timestamp when record created. |
| `updated_at` | Timestamp | System | Yes | Last modification time (immutable ledger stores change history). |

### Person (`persons`)
| Field | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `person_id` | UUID | Generated | Yes | Primary identifier. |
| `role` | Enum (`citizen`, `staff`, `inspector`, `admin`, `partner`) | Intake/HR | Yes | Role classification. |
| `first_name` | String | Intake/HR | Yes | Given name. |
| `last_name` | String | Intake/HR | Yes | Family name. |
| `email` | String | Intake/HR | No | Contact email; hashed for citizens per privacy rules. |
| `phone` | String | Intake/HR | No | E.164 formatted phone number. |
| `department` | String | HR | No | Department for staff/inspectors. |
| `created_at` | Timestamp | System | Yes | Record creation timestamp. |
| `updated_at` | Timestamp | System | Yes | Last update timestamp. |

### Assignment (`assignments`)
| Field | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `assignment_id` | UUID | Generated | Yes | Primary identifier. |
| `request_id` | UUID | Workflow | Yes | Foreign key to service request. |
| `assignee_id` | UUID | Workflow | Yes | Person responsible (staff or inspector). |
| `assigned_at` | Timestamp | Workflow | Yes | Time assignment created. |
| `due_at` | Timestamp | Workflow | No | Optional due date for the assignment. |
| `status` | Enum (`assigned`, `accepted`, `in_progress`, `completed`, `returned`) | Workflow | Yes | Assignment lifecycle state. |
| `notes` | Text | Workflow | No | Internal notes. |

### Audit Event (`audit_events`)
| Field | Type | Source | Required | Description |
|-------|------|--------|----------|-------------|
| `event_id` | UUID | Generated | Yes | Primary identifier. |
| `entity_type` | Enum (`service_request`, `assignment`, `person`, `attachment`) | System | Yes | Entity impacted. |
| `entity_id` | UUID | System | Yes | Identifier of impacted entity. |
| `action` | Enum (`create`, `update`, `delete`, `status_change`, `export`) | System | Yes | Action performed. |
| `actor_id` | UUID | System | Yes | Person or service account responsible. |
| `payload` | JSONB | System | Yes | Serialized diff or metadata. |
| `ip_address` | Inet | System | No | Source IP for security audits. |
| `created_at` | Timestamp | System | Yes | Event timestamp. |

## Derived & Analytical Fields
| Field | Type | Calculation | Notes |
|-------|------|-------------|-------|
| `response_time_minutes` | Integer | Difference between first staff assignment and request creation | Used for SLA reporting. |
| `resolution_time_minutes` | Integer | Difference between `status=resolved` timestamp and request creation | Displayed in dashboards. |
| `reopen_count` | Integer | Number of times status transitions from `closed`/`resolved` back to active states | Helps flag recurring issues. |
| `geo_bucket` | String | Spatial join of lat/long to hex bin | Supports geospatial heatmaps. |
| `sentiment_score` | Decimal | NLP score from citizen narrative | Optional feature, stored with provenance. |

## Data Lineage Notes
- **Intake API** is the system of record for `service_requests` and `attachments` at creation time.
- **Workflow Engine** appends to `assignments`, updates `status`, and triggers audit events.
- **Field Toolkit** synchronizes offline updates through the Workflow API; conflicts resolved using
  deterministic merge rules documented in `docs/acceptance-tests.md` (OP-003).
- **Reporting Warehouse** (dbt/Metabase) consumes the operational store via nightly snapshot and
  publishes curated datasets for dashboards and exports.

## Governance & Stewardship
- Data steward: **Operations Analytics Lead**.
- Schema authority: **Platform Engineering**.
- Change management: propose updates via data governance board; capture diffs in migration scripts
  and update this mapping.
- Privacy impact: personally identifiable information (PII) stored in hashed/encrypted form; refer to
  privacy assessment checklist in `docs/acceptance-tests.md` (NF-005).
