from django.contrib.auth.views import LoginView
from django.urls import path

from task_manager.views import IndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login")
]

app_name = "task_manager"
