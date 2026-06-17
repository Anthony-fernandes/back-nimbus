from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "entity_type", "entity_label", "actor_name", "created_at")
    list_filter = ("action", "entity_type", "origin")
    search_fields = ("action", "entity_label", "description", "actor_name")
    readonly_fields = [field.name for field in AuditLog._meta.fields]
