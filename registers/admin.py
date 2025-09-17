from django.contrib import admin

from . import models


@admin.register(models.Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(models.ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = (
        "register",
        "bundle_type",
        "scheduled_for",
        "completed",
        "created_at",
    )
    list_filter = ("bundle_type", "completed", "scheduled_for")
    search_fields = ("register__name", "notes")


@admin.register(models.Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("register", "schedule_entry", "remind_at", "is_sent")
    list_filter = ("is_sent", "remind_at")
    search_fields = ("register__name", "message")


class DocumentVersionInline(admin.TabularInline):
    model = models.DocumentVersion
    extra = 0
    fields = ("version", "file", "uploaded_by", "created_at")
    readonly_fields = ("version", "created_at")


@admin.register(models.Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "register", "created_at", "updated_at")
    search_fields = ("title", "register__name")
    inlines = [DocumentVersionInline]


@admin.register(models.ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("register", "action", "user", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("register__name", "details")
