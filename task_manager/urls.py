from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from task_manager.views import IndexView, TaskListView, TaskDetailView, TaskCreateView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("tasks/create/", TaskCreateView.as_view(), name="task_create")
]

app_name = "task_manager"
