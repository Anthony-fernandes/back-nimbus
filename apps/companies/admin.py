from django.contrib import admin

from .models import Company


BASE_READONLY_FIELDS = ("id", "created_at", "updated_at", "deleted_at")


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "document", "email", "phone", "is_active")
    search_fields = ("name", "document", "email", "phone")
    list_filter = ("is_active",)
    ordering = ("name",)
    readonly_fields = BASE_READONLY_FIELDS

