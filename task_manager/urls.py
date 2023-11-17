from django.urls import path

from task_manager.views import IndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
]

app_name = "task_manager"
