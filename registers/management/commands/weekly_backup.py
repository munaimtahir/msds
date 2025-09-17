"""Create a rolling archive of register documents."""

from __future__ import annotations

import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from registers.models import DocumentVersion


class Command(BaseCommand):
    help = "Create a weekly backup of document uploads retaining the last five copies."

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        archive_path = backup_dir / f"documents_{timestamp}.zip"

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for version in DocumentVersion.objects.select_related("document", "document__register"):
                if not version.file:
                    continue
                file_path = Path(version.file.path)
                if not file_path.exists():
                    continue
                register_slug = slugify(version.document.register.name) or f"register-{version.document.register_id}"
                document_slug = slugify(version.document.title) or f"document-{version.document_id}"
                arcname = f"{register_slug}/{document_slug}/v{version.version}_{file_path.name}"
                archive.write(file_path, arcname=arcname)

        backups = sorted(backup_dir.glob("documents_*.zip"))
        for old_backup in backups[:-5]:
            old_backup.unlink(missing_ok=True)

        self.stdout.write(self.style.SUCCESS(f"Created backup at {archive_path}"))
