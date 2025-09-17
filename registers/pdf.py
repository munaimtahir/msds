"""PDF generation utilities using WeasyPrint when available."""

from __future__ import annotations

from io import BytesIO
from typing import Iterable

from django.template import loader

try:  # pragma: no cover - optional dependency
    from weasyprint import HTML  # type: ignore

    HAS_WEASYPRINT = True
except Exception:  # pragma: no cover - gracefully fall back
    HAS_WEASYPRINT = False

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from .models import DocumentVersion, Register, ScheduleEntry


def _bundle_summary(entries: Iterable[ScheduleEntry]) -> str:
    lines = []
    for entry in entries:
        status = "Done" if entry.completed else "Pending"
        lines.append(f"- {entry.scheduled_for}: {status} ({entry.bundle_type})")
    return "\n".join(lines) or "No schedule entries recorded."


def _document_summary(documents: Iterable[DocumentVersion]) -> str:
    lines = []
    for version in documents:
        lines.append(f"- {version.document.title} v{version.version} ({version.filename})")
    return "\n".join(lines) or "No documents uploaded."


def render_register_pdf(register: Register) -> bytes:
    """Render a single page PDF summarising a register."""

    entries = register.schedule_entries.all().select_related("register")[:10]
    documents = (
        DocumentVersion.objects.filter(document__register=register)
        .select_related("document")
        .order_by("-created_at")[:10]
    )

    schedule_summary = _bundle_summary(entries)
    document_summary = _document_summary(documents)

    if HAS_WEASYPRINT:
        template = loader.get_template("registers/register_pdf.html")
        html = template.render(
            {
                "register": register,
                "schedule_summary": schedule_summary.replace("\n", "<br/>") or "",
                "document_summary": document_summary.replace("\n", "<br/>") or "",
            }
        )
        return HTML(string=html).write_pdf()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    textobject = pdf.beginText(margin, height - margin)
    textobject.setFont("Helvetica-Bold", 16)
    textobject.textLine(register.name)

    textobject.setFont("Helvetica", 12)
    textobject.textLine("")
    textobject.textLine("Schedule Overview:")
    for line in schedule_summary.split("\n"):
        textobject.textLine(line)

    textobject.textLine("")
    textobject.textLine("Documents:")
    for line in document_summary.split("\n"):
        textobject.textLine(line)

    pdf.drawText(textobject)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
