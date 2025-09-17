"""Views for the registers application."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    DigitalEntryForm,
    DocumentForm,
    DocumentVersionForm,
    RegisterSearchForm,
    ScheduleEntryForm,
)
from .models import ActivityLog, Register, ScheduleEntry
from .pdf import render_register_pdf


def _data_from_request(request: HttpRequest) -> dict[str, Any]:
    content_type = request.content_type or ""
    if content_type.startswith("application/json"):
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    if request.method == "GET":
        return request.GET.dict()
    return request.POST.dict()


def _current_user(request: HttpRequest):
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        return user
    return None


@method_decorator(csrf_exempt, name="dispatch")
class ScheduleEntryView(View):
    """Create or list schedule entries, grouped by bundle type."""

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        bundle_type = request.GET.get("bundle_type")
        qs = ScheduleEntry.objects.select_related("register")
        if bundle_type:
            qs = qs.filter(bundle_type=bundle_type)
        if request.GET.get("register"):
            qs = qs.filter(register_id=request.GET["register"])
        data = [
            {
                "id": entry.id,
                "register": entry.register.name,
                "bundle_type": entry.bundle_type,
                "scheduled_for": entry.scheduled_for.isoformat(),
                "completed": entry.completed,
            }
            for entry in qs.order_by("-scheduled_for")[:50]
        ]
        return JsonResponse({"results": data})

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        payload = _data_from_request(request)
        form = ScheduleEntryForm(payload)
        if form.is_valid():
            entry = form.save()
            ActivityLog.log(
                register=entry.register,
                schedule_entry=entry,
                action="created",
                details=f"{entry.get_bundle_type_display()} bundle scheduled for {entry.scheduled_for}",
            )
            return JsonResponse(
                {
                    "id": entry.id,
                    "message": "Schedule entry created",
                },
                status=201,
            )
        return JsonResponse({"errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class DigitalEntryView(View):
    """Capture digital register entries and store them as activity logs."""

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        payload = _data_from_request(request)
        form = DigitalEntryForm(payload)
        if form.is_valid():
            log = form.save(user=_current_user(request))
            return JsonResponse(
                {"id": log.id, "message": "Digital entry recorded"}, status=201
            )
        return JsonResponse({"errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class DocumentUploadView(View):
    """Handle scanned document uploads with automatic versioning."""

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        data = request.POST.copy()
        form = DocumentVersionForm(data, request.FILES)
        if form.is_valid():
            version = form.save(user=_current_user(request))
            ActivityLog.log(
                register=version.document.register,
                action="document_uploaded",
                details=f"Uploaded version {version.version} of {version.document.title}",
                user=_current_user(request),
            )
            return JsonResponse(
                {
                    "id": version.id,
                    "version": version.version,
                    "filename": version.filename,
                    "message": "Document uploaded",
                },
                status=201,
            )
        return JsonResponse({"errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class DocumentView(View):
    """Create base document containers prior to uploading scans."""

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        payload = _data_from_request(request)
        form = DocumentForm(payload)
        if form.is_valid():
            document = form.save()
            ActivityLog.log(
                register=document.register,
                action="created",
                details=f"Document container created for {document.title}",
                user=_current_user(request),
            )
            return JsonResponse({"id": document.id, "message": "Document created"}, status=201)
        return JsonResponse({"errors": form.errors}, status=400)


def generate_register_pdf_view(request: HttpRequest, pk: int) -> HttpResponse:
    register = get_object_or_404(Register, pk=pk)
    pdf_bytes = render_register_pdf(register)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    filename = f"register-{register.pk}.pdf"
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


def search_registers(request: HttpRequest) -> JsonResponse:
    form = RegisterSearchForm(request.GET or None)
    results: list[dict[str, Any]] = []
    if form.is_valid():
        filters = form.cleaned_filters()
        qs = Register.objects.prefetch_related("schedule_entries").filter(**filters)
        # Query filtering is already handled in cleaned_filters; do not duplicate here.
        # If you want to search description as well, move that logic to the form.
        qs = qs.distinct()
        for register in qs[:50]:
            results.append(
                {
                    "id": register.id,
                    "name": register.name,
                    "description": register.description,
                    "bundle_counts": {
                        key: register.schedule_entries.filter(bundle_type=key).count()
                        for key, _ in ScheduleEntry.BUNDLE_CHOICES
                    },
                }
            )
    else:
        return JsonResponse({"errors": form.errors}, status=400)
    return JsonResponse({"results": results})


def health_view(request: HttpRequest) -> JsonResponse:
    now = timezone.now()
    return JsonResponse({"status": "ok", "timestamp": now.isoformat()})


def pending_reminders(request: HttpRequest) -> JsonResponse:
    upcoming = timezone.now() + timedelta(days=7)
    reminders = (
        Register.objects.prefetch_related("reminders")
        .filter(reminders__remind_at__lte=upcoming, reminders__is_sent=False)
        .distinct()
    )
    data = []
    for register in reminders:
        for reminder in register.reminders.filter(
            remind_at__lte=upcoming, is_sent=False
        ).order_by("remind_at"):
            data.append(
                {
                    "register": register.name,
                    "remind_at": reminder.remind_at.isoformat(),
                    "message": reminder.message,
                }
            )
    return JsonResponse({"results": data})
