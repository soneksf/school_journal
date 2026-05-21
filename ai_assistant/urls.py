from django.urls import path
from . import views

app_name = "ai_assistant"

urlpatterns = [
    path("insights/", views.InsightListView.as_view(), name="insight_list"),
    path("insights/<int:pk>/", views.InsightDetailView.as_view(), name="insight_detail"),
    path("insights/request/<int:student_id>/", views.request_insight, name="request_insight"),
    path("chat/", views.chat_view, name="chat"),
    path("chat/<int:session_id>/", views.chat_view, name="chat"),
]
