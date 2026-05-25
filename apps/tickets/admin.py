from django.contrib import admin

from .models import Ticket


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "company",
        "client",
        "status",
        "priority",
        "requester",
        "sla_due_at",
        "due_at",
    )
    search_fields = (
        "code",
        "title",
        "company__name",
        "client__name",
        "requester",
        "category",
        "team",
    )
    list_filter = ("status", "priority", "type", "category", "company", "client")
    ordering = ("-created_at",)
    autocomplete_fields = ("company", "client", "project")
    filter_horizontal = ("technicians",)
    readonly_fields = BASE_READONLY_FIELDS

