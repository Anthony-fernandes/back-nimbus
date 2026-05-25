from django.contrib import admin

from .models import Sprint


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "project",
        "lead",
        "status",
        "start_at",
        "end_at",
        "capacity",
    )
    search_fields = (
        "name",
        "company__name",
        "project__name",
        "lead__username",
        "lead__first_name",
        "lead__last_name",
    )
    list_filter = ("status", "company")
    ordering = ("-start_at", "-created_at")
    autocomplete_fields = ("company", "project", "lead")
    readonly_fields = BASE_READONLY_FIELDS

