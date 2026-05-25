from django.contrib import admin

from .models import Activity


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "type",
        "status",
        "priority",
        "assignee",
        "project",
        "sprint",
        "due_at",
    )
    search_fields = (
        "title",
        "company__name",
        "assignee__username",
        "assignee__first_name",
        "assignee__last_name",
        "project__name",
        "ticket__code",
    )
    list_filter = ("status", "priority", "type", "company")
    ordering = ("-created_at",)
    autocomplete_fields = ("company", "assignee", "project", "sprint", "ticket")
    readonly_fields = BASE_READONLY_FIELDS

