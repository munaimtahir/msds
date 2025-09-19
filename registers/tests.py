from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .forms import DigitalEntryForm, RegisterSearchForm
from .models import (
    ActivityLog,
    Document,
    DocumentVersion,
    Register,
    Reminder,
    ScheduleEntry,
)
from .pdf import render_register_pdf


class MediaRootCleanupMixin:
    def tearDown(self) -> None:  # pragma: no cover - simple filesystem cleanup
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            shutil.rmtree(media_root)
        super().tearDown()


class ModelMethodTests(TestCase):
    def test_register_defaults_to_active(self) -> None:
        register = Register.objects.create(name="Archive Register")
        self.assertTrue(register.is_active)

    def test_schedule_entry_mark_complete_sets_timestamp(self) -> None:
        register = Register.objects.create(name="Daily Duties")
        entry = ScheduleEntry.objects.create(
            register=register,
            bundle_type=ScheduleEntry.DAILY,
            scheduled_for=timezone.now().date(),
        )
        before = timezone.now()
        entry.mark_complete()
        entry.refresh_from_db()

        self.assertTrue(entry.completed)
        self.assertIsNotNone(entry.completed_at)
        self.assertGreaterEqual(entry.completed_at, before)

    def test_reminder_mark_sent_sets_flag(self) -> None:
        register = Register.objects.create(name="Reminder Register")
        reminder = Reminder.objects.create(
            register=register,
            remind_at=timezone.now(),
            message="Send notice",
        )

        reminder.mark_sent()
        reminder.refresh_from_db()

        self.assertTrue(reminder.is_sent)


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "test_media")
class RegisterFeatureTests(MediaRootCleanupMixin, TestCase):

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


@override_settings(MEDIA_ROOT=settings.BASE_DIR / "test_media")
class ActivityLogIntegrationTests(MediaRootCleanupMixin, TestCase):
    def test_schedule_entry_view_logs_creation(self) -> None:
        register = Register.objects.create(name="Integration Register")
        url = reverse("registers:bundle-list-create")
        payload = {
            "register": register.pk,
            "bundle_type": ScheduleEntry.DAILY,
            "scheduled_for": timezone.now().date(),
            "notes": "Prepare reports",
        }

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)

        entry = ScheduleEntry.objects.get(register=register)
        log = ActivityLog.objects.get(schedule_entry=entry)
        self.assertEqual(log.action, "created")
        self.assertEqual(log.register, register)
        self.assertEqual(
            log.details,
            f"{entry.get_bundle_type_display()} bundle scheduled for {entry.scheduled_for}",
        )

    def test_digital_entry_form_save_logs_activity(self) -> None:
        register = Register.objects.create(name="Digital Register")
        schedule_entry = ScheduleEntry.objects.create(
            register=register,
            bundle_type=ScheduleEntry.WEEKLY,
            scheduled_for=timezone.now().date(),
        )
        form = DigitalEntryForm(
            data={
                "register": register.pk,
                "schedule_entry": schedule_entry.pk,
                "message": "Completed weekly review",
            }
        )
        self.assertTrue(form.is_valid())
        user = get_user_model().objects.create_user("auditor")

        log = form.save(user=user)

        self.assertEqual(log.action, "digital_entry")
        self.assertEqual(log.register, register)
        self.assertEqual(log.schedule_entry, schedule_entry)
        self.assertEqual(log.details, "Completed weekly review")
        self.assertEqual(log.user, user)

    def test_document_upload_view_logs_activity(self) -> None:
        user = get_user_model().objects.create_user("records")
        register = Register.objects.create(name="Document Register")
        document = Document.objects.create(register=register, title="Inspection Form")
        upload = SimpleUploadedFile("scan.pdf", b"%PDF-1.4 test content")

        self.client.force_login(user)
        response = self.client.post(
            reverse("registers:document-upload"),
            {"document": document.pk, "file": upload, "notes": "Initial upload"},
        )
        self.assertEqual(response.status_code, 201)

        version = DocumentVersion.objects.get(document=document)
        log = ActivityLog.objects.get(action="document_uploaded")
        self.assertEqual(log.register, register)
        self.assertEqual(log.user, user)
        self.assertEqual(
            log.details,
            f"Uploaded version {version.version} of {document.title}",
        )


class RegisterSearchTests(TestCase):
    def test_cleaned_filters_returns_expected_mapping(self) -> None:
        form = RegisterSearchForm(
            data={
                "query": "alpha",
                "bundle_type": ScheduleEntry.DAILY,
                "completed": "true",
            }
        )
        self.assertTrue(form.is_valid())

        filters = form.cleaned_filters()
        self.assertEqual(
            filters,
            {
                "schedule_entries__bundle_type": ScheduleEntry.DAILY,
                "schedule_entries__completed": True,
            },
        )
        self.assertNotIn("query", filters)

    def test_search_view_filters_by_bundle_completion_and_query(self) -> None:
        alpha = Register.objects.create(name="Alpha")
        ScheduleEntry.objects.create(
            register=alpha,
            bundle_type=ScheduleEntry.DAILY,
            scheduled_for=timezone.now().date(),
            completed=True,
        )
        beta = Register.objects.create(name="Beta")
        ScheduleEntry.objects.create(
            register=beta,
            bundle_type=ScheduleEntry.WEEKLY,
            scheduled_for=timezone.now().date(),
            completed=False,
        )
        gamma = Register.objects.create(name="Gamma")
        ScheduleEntry.objects.create(
            register=gamma,
            bundle_type=ScheduleEntry.DAILY,
            scheduled_for=timezone.now().date(),
            completed=False,
        )
        delta = Register.objects.create(name="Delta")
        ScheduleEntry.objects.create(
            register=delta,
            bundle_type=ScheduleEntry.DAILY,
            scheduled_for=timezone.now().date(),
            completed=False,
        )

        response = self.client.get(
            reverse("registers:search"),
            {
                "query": "gam",
                "bundle_type": ScheduleEntry.DAILY,
                "completed": "false",
            },
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["id"], gamma.id)
        self.assertEqual(result["name"], "Gamma")
        self.assertEqual(result["bundle_counts"][ScheduleEntry.DAILY], 1)
        self.assertEqual(result["bundle_counts"][ScheduleEntry.WEEKLY], 0)


class WeeklyBackupCommandTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        base_dir = Path(self.temp_dir.name)
        self.override = override_settings(
            BASE_DIR=base_dir,
            MEDIA_ROOT=base_dir / "media",
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

    def test_weekly_backup_reduces_archives_to_latest_five(self) -> None:
        register = Register.objects.create(name="Archive Source")
        document = Document.objects.create(register=register, title="Safety Manual")
        file_upload = SimpleUploadedFile("manual.txt", b"procedures")
        DocumentVersion.objects.create(document=document, file=file_upload)

        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for index in range(7):
            archive_name = backup_dir / f"documents_2023010{index}.zip"
            with zipfile.ZipFile(archive_name, "w") as archive:
                archive.writestr("placeholder.txt", "data")

        call_command("weekly_backup")

        backups = sorted(backup_dir.glob("documents_*.zip"))
        self.assertEqual(len(backups), 5)
        latest_backup = max(backups)

        version = DocumentVersion.objects.get(document=document)
        expected_arcname = (
            f"{slugify(register.name)}/{slugify(document.title)}/"
            f"v{version.version}_{Path(version.file.path).name}"
        )
        with zipfile.ZipFile(latest_backup, "r") as archive:
            self.assertIn(expected_arcname, archive.namelist())
