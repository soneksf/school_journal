from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile_edit, name="profile_edit"),

    path("password_change/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/password_change.html",
        success_url="/accounts/profile/",
    ), name="password_change"),

    path("students/", views.StudentListView.as_view(), name="student_list"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="student_detail"),
    path("teachers/", views.TeacherListView.as_view(), name="teacher_list"),
    path("teachers/<int:pk>/", views.TeacherDetailView.as_view(), name="teacher_detail"),
]
