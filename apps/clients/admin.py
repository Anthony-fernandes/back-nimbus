from django.contrib import admin

from .models import Client


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "email", "phone", "status", "health", "plan")
    search_fields = (
        "name",
        "company__name",
        "email",
        "phone",
        "contact_name",
        "sector",
    )
    list_filter = ("status", "health", "plan", "company")
    ordering = ("name",)
    autocomplete_fields = ("company",)
    readonly_fields = BASE_READONLY_FIELDS

