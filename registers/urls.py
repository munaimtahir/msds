"""URL configuration for the registers app."""

from django.urls import path

from . import views

app_name = "registers"

urlpatterns = [
    path("bundles/", views.ScheduleEntryView.as_view(), name="bundle-list-create"),
    path("digital-entry/", views.DigitalEntryView.as_view(), name="digital-entry"),
    path("documents/", views.DocumentView.as_view(), name="document-create"),
    path("documents/upload/", views.DocumentUploadView.as_view(), name="document-upload"),
    path("registers/<int:pk>/pdf/", views.generate_register_pdf_view, name="register-pdf"),
    path("search/", views.search_registers, name="search"),
    path("reminders/", views.pending_reminders, name="pending-reminders"),
    path("health/", views.health_view, name="health"),
]
