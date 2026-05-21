from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "recipient", "kind", "channel", "title", "is_read", "sent_at")
    list_filter = ("kind", "channel", "is_read")
    search_fields = ("title", "body", "recipient__username")
    date_hierarchy = "created_at"
