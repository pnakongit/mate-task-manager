from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from task_manager.views import (IndexView,
                                TaskListView,
                                TaskDetailView,
                                TaskCreateView,
                                TaskUpdateView,
                                TaskDeleteView,
                                ProjectListView,
                                ProjectDetailView,
                                ProjectCreateView,
                                ProjectUpdateView,
                                ProjectDeleteView,
                                TeamListView,
                                TeamDetailView,
                                TeamCreateView,
                                TeamUpdateView,
                                TeamDeleteView,
                                WorkerListView,
                                WorkerDetailView,
                                WorkerCreateView,
                                WorkerUpdateView)

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("tasks/create/", TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/update/", TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("projects/", ProjectListView.as_view(), name="project_list"),
    path("projects/<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
    path("projects/create/", ProjectCreateView.as_view(), name="project_create"),
    path("projects/<int:pk>/update/", ProjectUpdateView.as_view(), name="project_update"),
    path("projects/<int:pk>/delete/", ProjectDeleteView.as_view(), name="project_delete"),
    path("teams/", TeamListView.as_view(), name="team_list"),
    path("teams/<int:pk>/", TeamDetailView.as_view(), name="team_detail"),
    path("teams/create/", TeamCreateView.as_view(), name="team_create"),
    path("teams/<int:pk>/update/", TeamUpdateView.as_view(), name="team_update"),
    path("teams/<int:pk>/delete/", TeamDeleteView.as_view(), name="team_delete"),
    path("workers/", WorkerListView.as_view(), name="worker_list"),
    path("workers/<int:pk>", WorkerDetailView.as_view(), name="worker_detail"),
    path("workers/create/", WorkerCreateView.as_view(), name="worker_create"),
    path("workers/<int:pk>/update/", WorkerUpdateView.as_view(), name="worker_update")
]

app_name = "task_manager"
