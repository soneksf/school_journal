from django.contrib import admin

from .models import ChatMessage, ChatSession, StudentInsight


@admin.register(StudentInsight)
class StudentInsightAdmin(admin.ModelAdmin):
    list_display = ("created_at", "student", "status", "risk_level", "requested_by")
    list_filter = ("status", "risk_level")
    search_fields = ("student__user__last_name", "summary")
    readonly_fields = ("raw_response", "created_at", "completed_at")


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "title", "updated_at")
    search_fields = ("title", "user__username")
    inlines = [ChatMessageInline]
