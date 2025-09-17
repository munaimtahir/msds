"""Forms used by the registers application."""

from __future__ import annotations

import json
from typing import Any

from django import forms

from .models import ActivityLog, Document, DocumentVersion, Register, ScheduleEntry


class RegisterSearchForm(forms.Form):
    query = forms.CharField(required=False, label="Search term")
    bundle_type = forms.ChoiceField(
        choices=(("", "All"),) + tuple(ScheduleEntry.BUNDLE_CHOICES),
        required=False,
    )
    completed = forms.TypedChoiceField(
        required=False,
        choices=(
            ("", "All"),
            ("true", "Completed"),
            ("false", "Outstanding"),
        ),
        coerce=lambda value: {"true": True, "false": False}.get(value, None),
    )

    def cleaned_filters(self) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if self.cleaned_data.get("bundle_type"):
            filters["schedule_entries__bundle_type"] = self.cleaned_data["bundle_type"]
        if self.cleaned_data.get("completed") is not None:
            filters["schedule_entries__completed"] = self.cleaned_data["completed"]
        if self.cleaned_data.get("query"):
            filters["name__icontains"] = self.cleaned_data["query"]
        return filters


class ScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = ScheduleEntry
        fields = ["register", "bundle_type", "scheduled_for", "notes"]
        widgets = {
            "scheduled_for": forms.DateInput(attrs={"type": "date"}),
        }


class DigitalEntryForm(forms.Form):
    register = forms.ModelChoiceField(queryset=Register.objects.all())
    schedule_entry = forms.ModelChoiceField(
        queryset=ScheduleEntry.objects.all(), required=False
    )
    message = forms.CharField(widget=forms.Textarea)

    def save(self, user=None) -> ActivityLog:
        register = self.cleaned_data["register"]
        schedule_entry = self.cleaned_data.get("schedule_entry")
        message = self.cleaned_data["message"]
        return ActivityLog.log(
            register=register,
            schedule_entry=schedule_entry,
            action="digital_entry",
            details=message,
            user=user,
        )


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["register", "title", "description"]


class DocumentVersionForm(forms.ModelForm):
    metadata = forms.CharField(required=False, help_text="Optional JSON metadata")

    class Meta:
        model = DocumentVersion
        fields = ["document", "file", "notes"]

    def clean_metadata(self) -> dict[str, Any]:
        raw = self.cleaned_data.get("metadata")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:  # pragma: no cover - form validation handles message
            raise forms.ValidationError("Metadata must be valid JSON") from exc

    def save(self, user=None, commit: bool = True) -> DocumentVersion:
        version = super().save(commit=False)
        version.uploaded_by = user
        if commit:
            version.save()
        return version
