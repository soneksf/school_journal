from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.AbsenceListView.as_view(), name="absence_list"),
    path("new/", views.AbsenceCreateView.as_view(), name="absence_create"),
    path("<int:pk>/edit/", views.AbsenceUpdateView.as_view(), name="absence_update"),
]
