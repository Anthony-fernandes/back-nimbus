from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "category", "event", "is_read", "created_at")
    list_filter = ("category", "is_read", "is_archived", "is_favorite")
    search_fields = ("title", "message", "actor_name")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "inbox_enabled", "digest_frequency")
    list_filter = ("email_enabled", "inbox_enabled")
