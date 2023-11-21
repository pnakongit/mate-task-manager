import datetime
from typing import Any

from django.views.generic import TemplateView

from task_manager.models import Task, Activity


class IndexView(TemplateView):
    number_of_last_tasks = 10
    number_of_last_activity = 10
    template_name = "task_manager/index.html"

    def get_context_data(self, **kwargs) -> dict[str: Any]:
        kwargs = super().get_context_data(**kwargs)
        user_team = self.request.user.team

        context = {
            "last_tasks": Task.objects.filter(
                project__teams=user_team
            ).order_by("-created_time")[:self.number_of_last_tasks].prefetch_related("assignees"),
            "last_activity": Activity.objects.filter(
                task__project__teams=user_team
            ).order_by("-created_time"),
            "count_unfinished_tasks": Task.objects.filter(
                project__teams=user_team, is_completed=False
            ).count(),
            "count_unassigned_tasks": Task.objects.filter(
                project__teams=user_team, assignees__isnull=True,
            ).count(),
            "count_over_deadline_tasks": Task.objects.filter(
                project__teams=user_team, deadline__gt=datetime.date.today()
            ).count()
        }

        kwargs.update(context)

        return kwargs
