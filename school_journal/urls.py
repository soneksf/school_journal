"""Root URL configuration for the school_journal project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("school_core.urls", "school_core"), namespace="school_core")),
    path("grades/", include(("grades.urls", "grades"), namespace="grades")),
    path("attendance/", include(("attendance.urls", "attendance"), namespace="attendance")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),
    path("ai/", include(("ai_assistant.urls", "ai_assistant"), namespace="ai_assistant")),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
