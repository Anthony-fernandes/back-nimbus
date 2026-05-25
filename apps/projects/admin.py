from django.contrib import admin

from .models import Project


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "client",
        "status",
        "owner",
        "progress",
        "budget",
        "due_at",
    )
    search_fields = (
        "name",
        "company__name",
        "client__name",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    )
    list_filter = ("status", "company", "client")
    ordering = ("-created_at",)
    autocomplete_fields = ("company", "client", "owner")
    filter_horizontal = ("team",)
    readonly_fields = BASE_READONLY_FIELDS

