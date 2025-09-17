from __future__ import annotations

import shutil
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Document, DocumentVersion, Register, Reminder, ScheduleEntry
from .pdf import render_register_pdf


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "test_media")
class RegisterFeatureTests(TestCase):
    def tearDown(self) -> None:
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            shutil.rmtree(media_root)

    def test_schedule_entry_creation_api(self) -> None:
        register = Register.objects.create(name="Daily Log")
        url = reverse("registers:bundle-list-create")
        payload = {
            "register": register.pk,
            "bundle_type": ScheduleEntry.DAILY,
            "scheduled_for": timezone.now().date(),
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ScheduleEntry.objects.count(), 1)

    def test_document_version_auto_increment(self) -> None:
        register = Register.objects.create(name="Documented Register")
        document = Document.objects.create(register=register, title="Manual")

        file1 = SimpleUploadedFile("scan1.pdf", b"filecontent")
        version1 = DocumentVersion(document=document, file=file1)
        version1.save()

        file2 = SimpleUploadedFile("scan2.pdf", b"filecontent2")
        version2 = DocumentVersion(document=document, file=file2)
        version2.save()

        self.assertEqual(version1.version, 1)
        self.assertEqual(version2.version, 2)

    def test_generate_reminders_command(self) -> None:
        register = Register.objects.create(name="Reminder Register")
        ScheduleEntry.objects.create(
            register=register,
            bundle_type=ScheduleEntry.WEEKLY,
            scheduled_for=timezone.now().date(),
        )

        call_command("generate_reminders", days=3)
        self.assertEqual(Reminder.objects.count(), 1)

    def test_pdf_generation_returns_bytes(self) -> None:
        register = Register.objects.create(name="PDF Register")
        ScheduleEntry.objects.create(
            register=register,
            bundle_type=ScheduleEntry.DAILY,
            scheduled_for=timezone.now().date(),
        )

        pdf_bytes = render_register_pdf(register)
        self.assertTrue(pdf_bytes)
        self.assertIsInstance(pdf_bytes, (bytes, bytearray))
