from django.urls import path
from . import views

app_name = "grades"

urlpatterns = [
    path("", views.GradeListView.as_view(), name="grade_list"),
    path("new/", views.GradeCreateView.as_view(), name="grade_create"),
    path("<int:pk>/edit/", views.GradeUpdateView.as_view(), name="grade_update"),
    path("report/<int:student_id>/", views.student_report, name="student_report"),
]
