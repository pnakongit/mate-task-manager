from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from task_manager.views import IndexView, TaskList

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("tasks/", TaskList.as_view(), name="task_list")
]

app_name = "task_manager"
