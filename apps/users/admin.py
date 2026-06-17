from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PermissionBlock, User


@admin.register(PermissionBlock)
class PermissionBlockAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "active", "created_at")
    list_filter = ("company", "active")
    search_fields = ("name", "description", "company__name")
    ordering = ("name",)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "company",
        "client",
        "role",
        "is_staff",
        "is_active",
    )
    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "company__name",
        "client__name",
        "job_title",
        "specialty",
        "technical_group",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "company", "client")
    ordering = ("username",)
    autocomplete_fields = ("company", "client")
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Informacoes adicionais",
            {
                "fields": (
                    "company",
                    "client",
                    "role",
                    "job_title",
                    "specialty",
                    "phone",
                    "total_hours",
                    "used_hours",
                    "technical_group",
                    "permissions_json",
                    "granted_permissions",
                    "denied_permissions",
                    "permission_blocks",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "Informacoes adicionais",
            {
                "classes": ("wide",),
                "fields": (
                    "company",
                    "client",
                    "role",
                    "job_title",
                    "specialty",
                    "phone",
                    "total_hours",
                    "used_hours",
                    "technical_group",
                    "permissions_json",
                    "granted_permissions",
                    "denied_permissions",
                    "permission_blocks",
                ),
            },
        ),
    )
