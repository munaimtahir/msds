# msds

This project contains a Django implementation of a registers management service.

## Key features

* Register models for schedules, reminders, document versioning and activity logs.
* JSON based APIs for creating daily/weekly/pending bundles, digital entries and document uploads.
* Support for generating single-page A4 PDFs using WeasyPrint when available, with a ReportLab fallback.
* Search and filter endpoints plus a `/health` status response.
* Management commands for reminder generation and rolling weekly backups retaining the last five archives.

## Running locally

```bash
python manage.py migrate
python manage.py runserver
```

The main API is exposed under `/api/registers/`. Useful endpoints include:

| Endpoint | Description |
| --- | --- |
| `POST /api/registers/bundles/` | Create a scheduled bundle entry (daily/weekly/pending). |
| `GET /api/registers/bundles/` | List schedule entries, optionally filtered by `bundle_type` or `register`. |
| `POST /api/registers/digital-entry/` | Record a digital register entry. |
| `POST /api/registers/documents/` | Create a document container before uploading scans. |
| `POST /api/registers/documents/upload/` | Upload a document scan with automatic versioning. |
| `GET /api/registers/registers/<id>/pdf/` | Download an A4 PDF summary for the given register. |
| `GET /api/registers/search/` | Search registers by text, bundle type and completion status. |
| `GET /api/registers/reminders/` | Inspect reminders scheduled within the next seven days. |
| `GET /api/registers/health/` | Lightweight health check returning a timestamp. |

### Management commands

```bash
python manage.py generate_reminders  # create reminders for upcoming schedule entries
python manage.py weekly_backup       # archive document uploads, keeping the last five copies
```