import datetime
from typing import Any, Optional

from django.db.models import QuerySet, Q
from django.views import generic

from task_manager.forms import TaskFilterForm
from task_manager.models import Task, Activity


class IndexView(generic.TemplateView):
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


class TaskListView(generic.ListView):
    model = Task
    paginate_by = 4
    filter_form = TaskFilterForm

    def get_paginate_by(self, queryset: QuerySet) -> int:
        tasks_on_page = self.request.GET.get("tasks_on_page")
        if tasks_on_page and tasks_on_page.isdigit():
            self.request.session["tasks_on_page"] = int(tasks_on_page)
        return self.request.session.get("tasks_on_page") or self.paginate_by

    def get_context_data(
            self,
            *,
            object_list: Optional[Any] = None,
            **kwargs: Any
    ) -> dict[str: Any]:
        context = super().get_context_data(object_list=object_list, **kwargs)

        form = self.filter_form(self.request.GET, user=self.request.user)
        context["filter"] = form

        return context

    def get_filters(self) -> Q:

        form = self.filter_form(self.request.GET, user=self.request.user)
        filters = Q()
        if form.is_valid():
            for field, value in form.cleaned_data.items():
                if value:
                    filters &= Q(**{field: value})

        return filters

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        queryset = queryset.filter(project__teams__workers=self.request.user)

        filters = self.get_filters()

        if filters:
            return queryset.filter(filters)

        return queryset
