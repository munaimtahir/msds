# Usage Examples & Operational Runbooks

This document provides guided walkthroughs for common MSDS workflows across staff, administrators,
and compliance teams. Scripts and automation snippets referenced here should be version-controlled in
this repository alongside application code.

## Table of Contents
- [Staff Workflows](#staff-workflows)
  - [Triage & Assignment](#triage--assignment)
  - [Field Inspection Sync](#field-inspection-sync)
  - [Escalating SLA Breaches](#escalating-sla-breaches)
- [Administrator Workflows](#administrator-workflows)
  - [User Provisioning](#user-provisioning)
  - [Configuration Changes](#configuration-changes)
- [Backup Procedures](#backup-procedures)
  - [Operational Database Backup](#operational-database-backup)
  - [Object Storage Snapshot](#object-storage-snapshot)
  - [Disaster Recovery Verification](#disaster-recovery-verification)
- [Audit Export Processes](#audit-export-processes)
  - [Scheduled Nightly Export](#scheduled-nightly-export)
  - [Ad Hoc Case Packet](#ad-hoc-case-packet)
  - [Transparency Portal Publication](#transparency-portal-publication)

## Staff Workflows
### Triage & Assignment
1. Log in to the Operations Console and open the **New Requests** queue.
2. Review each request summary, attachments, and map location.
3. Click **Validate** to confirm channel metadata; corrections create `audit_events` with `action=update`.
4. Assign to a staff unit:
   - Click **Assign** → select `Department` and `Assignee`.
   - Set priority and SLA override if needed.
   - Optionally attach standard response templates.
5. Outcome: `assignments` table records a new row; request `status` transitions to `assigned`.
6. Acceptance tests: refer to `OP-001`, `OP-002` in `docs/acceptance-tests.md`.

### Field Inspection Sync
1. Inspector opens the Field Toolkit mobile app and downloads their queue before going offline.
2. During inspection, updates findings, photos, and status changes.
3. Upon reconnecting, app syncs with Workflow API. Conflicts resolved per last-write-wins; conflicting
   attributes flagged for supervisor review.
4. Supervisor reviews sync report within Operations Console → **Sync Reconciliation** tab.
5. Outcome: offline events produce `audit_events` with actor = inspector; case timeline shows merged
   history.
6. Monitor using dashboard widget **Offline Sync Success Rate**.

### Escalating SLA Breaches
1. From Operations Console, open **SLA Watchlist** filter (requests with `sla_due_at` < 24 hours).
2. Trigger **Escalate** action to notify supervisors via email/SMS and add `priority=critical`.
3. System generates Temporal workflow signal to expedite scheduling.
4. If unresolved past SLA, automatic status change to `waiting_external` or `in_progress` with reason.
5. Document manual follow-up notes in request timeline for audit compliance.

## Administrator Workflows
### User Provisioning
1. Navigate to **Admin → User Management**.
2. Click **Invite User** and supply name, email, department, and role (`staff`, `inspector`, `admin`).
3. System sends invitation email with activation link; upon acceptance, user appears in `persons` table.
4. For API-only accounts, generate service tokens under **Admin → API Clients**. Store secrets in vault.
5. Deactivate accounts via **Suspend** to preserve history while revoking access.

### Configuration Changes
1. Access **Admin → Configuration → Taxonomy** to adjust service categories.
2. Changes trigger versioned configuration stored in `config/service-taxonomy.yaml`.
3. Platform automatically redeploys workflow rules using CI pipeline; review pipeline status before
   confirming release.
4. Document changes in change-log channel and update training materials as needed.

## Backup Procedures
### Operational Database Backup
- Nightly job executed via `cron` on VPS or GitHub Actions workflow:
  ```bash
  pg_dump --format=custom --file=/backups/msds-$(date +%Y%m%d).dump $DATABASE_URL
  aws s3 cp /backups/msds-$(date +%Y%m%d).dump s3://msds-backups/ --sse AES256
  ```
- Retain 30 days of nightly backups, 12 monthly archives.
- Verify checksums using `sha256sum` and store results in the backup log table `backup_runs`.

### Object Storage Snapshot
- Use lifecycle policies to transition attachments to Glacier after 90 days.
- Weekly job exports manifest of new/updated objects:
  ```bash
  aws s3 ls s3://msds-attachments --recursive --human-readable \
    --summarize > reports/attachments-$(date +%Y%m%d).txt
  ```
- Commit manifests to the repository for traceability when feasible (mask PII before commit).

### Disaster Recovery Verification
1. Restore latest database dump into staging environment.
2. Rehydrate object storage manifest to ensure references remain valid.
3. Run smoke tests (`IN-001`, `OP-001`, `RA-001`) to confirm functional parity.
4. Document results in `docs/dr-runbooks/` (create dated subfolder per drill).

## Audit Export Processes
### Scheduled Nightly Export
1. Temporal workflow `audit_export_nightly` triggers at 02:00 local time.
2. Workflow executes dbt models `audit_case_snapshot` and `audit_assignment_snapshot`.
3. Export results zipped, encrypted (AES-256), and uploaded to S3 `s3://msds-audit-exports/YYYY/MM/DD/`.
4. Metadata recorded in `audit_events` (`action=export`) and `export_runs` table with checksum.
5. Distribution email with download link sent to compliance team; link expires in 7 days.

### Ad Hoc Case Packet
1. Auditor selects case(s) within Operations Console → **Generate Audit Packet**.
2. Backend compiles request details, attachments, communication logs, and assignment history into PDF.
3. Auditor receives download; event logged with `action=export` and actor reference.
4. Optional: push packet to secure document management system via webhook.

### Transparency Portal Publication
1. Weekly job sanitizes dataset (remove PII, aggregate sensitive fields).
2. Data pushed to open-data portal (e.g., Socrata) using API token stored in secrets manager.
3. Post-publication validation ensures row counts and schema match expectation; results stored in
   `transparency_publication_logs` table.
4. Notify communications team via Slack with release notes and changelog link.

## Version Control Practices
- Store automation scripts (e.g., `backup/`, `scripts/exports/`) in repository with clear README.
- Use semantic versioning tags (e.g., `v1.2.0`) to tie operational runbooks to release snapshots.
- Update this document whenever workflows change; cross-reference acceptance tests to maintain
  alignment.
