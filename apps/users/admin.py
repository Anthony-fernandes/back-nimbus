from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "company",
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
        "job_title",
        "specialty",
        "technical_group",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "company")
    ordering = ("username",)
    autocomplete_fields = ("company",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Informacoes adicionais",
            {
                "fields": (
                    "company",
                    "role",
                    "job_title",
                    "specialty",
                    "phone",
                    "total_hours",
                    "used_hours",
                    "technical_group",
                    "permissions_json",
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
                    "role",
                    "job_title",
                    "specialty",
                    "phone",
                    "total_hours",
                    "used_hours",
                    "technical_group",
                    "permissions_json",
                ),
            },
        ),
    )
