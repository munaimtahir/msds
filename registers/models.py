from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class TimeStampedModel(models.Model):
    """Abstract base class providing created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Register(TimeStampedModel):
    """Represents a physical or digital register that requires tracking."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.name


class ScheduleEntry(TimeStampedModel):
    """An individual scheduled entry belonging to a register."""

    DAILY = "daily"
    WEEKLY = "weekly"
    PENDING = "pending"

    BUNDLE_CHOICES = [
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (PENDING, "Pending"),
    ]

    register = models.ForeignKey(
        Register, related_name="schedule_entries", on_delete=models.CASCADE
    )
    bundle_type = models.CharField(max_length=10, choices=BUNDLE_CHOICES)
    scheduled_for = models.DateField()
    notes = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-scheduled_for", "-created_at"]
        indexes = [
            models.Index(fields=["bundle_type", "scheduled_for"]),
        ]

    def mark_complete(self) -> None:
        self.completed = True
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at", "updated_at"])


class Reminder(TimeStampedModel):
    """Represents a reminder message for upcoming schedule entries."""

    register = models.ForeignKey(
        Register, related_name="reminders", on_delete=models.CASCADE
    )
    schedule_entry = models.ForeignKey(
        "ScheduleEntry",
        related_name="reminders",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    remind_at = models.DateTimeField()
    message = models.CharField(max_length=255)
    is_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ["remind_at"]

    def mark_sent(self) -> None:
        self.is_sent = True
        self.save(update_fields=["is_sent", "updated_at"])


class Document(TimeStampedModel):
    """Container for uploaded documents associated with a register."""

    register = models.ForeignKey(
        Register, related_name="documents", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]
        unique_together = (("register", "title"),)

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.title

    def latest_version(self) -> "DocumentVersion | None":
        return self.versions.order_by("-version").first()

    def next_version_number(self) -> int:
        latest = self.latest_version()
        return (latest.version if latest else 0) + 1


class DocumentVersion(TimeStampedModel):
    """Individual file instances for a :class:`Document`."""

    document = models.ForeignKey(
        Document, related_name="versions", on_delete=models.CASCADE
    )
    version = models.PositiveIntegerField(default=0)
    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    uploaded_by = models.ForeignKey(
        User, related_name="uploaded_documents", null=True, blank=True, on_delete=models.SET_NULL
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("document", "version")
        ordering = ["-version", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.version:
            self.version = self.document.next_version_number()
        super().save(*args, **kwargs)

    @property
    def filename(self) -> str:
        return self.file.name.split("/")[-1]


class ActivityLog(TimeStampedModel):
    """Tracks user activity for auditing changes to registers."""

    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("digital_entry", "Digital Entry"),
        ("document_uploaded", "Document Uploaded"),
    ]

    register = models.ForeignKey(
        Register, related_name="activity_logs", on_delete=models.CASCADE
    )
    schedule_entry = models.ForeignKey(
        ScheduleEntry,
        related_name="activity_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(
        User, related_name="register_activity", null=True, blank=True, on_delete=models.SET_NULL
    )
    details = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def describe(self) -> str:
        timestamp = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M")
        return f"[{timestamp}] {self.get_action_display()} - {self.details or 'No details'}"

    @classmethod
    def log(
        cls,
        *,
        register: Register,
        action: str,
        details: str = "",
        user: User | None = None,
        schedule_entry: ScheduleEntry | None = None,
    ) -> "ActivityLog":
        return cls.objects.create(
            register=register,
            action=action,
            details=details,
            user=user,
            schedule_entry=schedule_entry,
        )
