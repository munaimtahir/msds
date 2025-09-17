"""Management command for creating reminders for upcoming schedule entries."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from registers.models import Reminder, ScheduleEntry


class Command(BaseCommand):
    help = "Generate reminders for schedule entries occurring within the next week."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days in advance to generate reminders for.",
        )

    def handle(self, *args, **options):
        horizon = options["days"]
        now = timezone.now()
        cutoff = now + timedelta(days=horizon)

        created_count = 0
        for entry in ScheduleEntry.objects.filter(
            scheduled_for__range=(now.date(), cutoff.date())
        ).select_related("register"):
            remind_at = datetime.combine(entry.scheduled_for, time(9, 0))
            if timezone.is_naive(remind_at):
                remind_at = timezone.make_aware(remind_at)
            reminder, created = Reminder.objects.get_or_create(
                schedule_entry=entry,
                defaults={
                    "register": entry.register,
                    "remind_at": remind_at,
                    "message": f"Reminder: {entry.register.name} {entry.get_bundle_type_display()} due {entry.scheduled_for}",
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Generated {created_count} reminders."))
