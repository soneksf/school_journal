from django.urls import path
from . import views

app_name = "school_core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("classes/", views.ClassListView.as_view(), name="class_list"),
    path("classes/<int:pk>/", views.ClassDetailView.as_view(), name="class_detail"),
    path("subjects/", views.SubjectListView.as_view(), name="subject_list"),
]
