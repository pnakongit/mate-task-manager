import datetime
from typing import Any, Optional

from django.db import transaction
from django.db.models import QuerySet, Q
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from task_manager.forms import TaskFilterForm, CommentForm
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
            ).order_by("-created_time")[:self.number_of_last_activity],
            "count_unfinished_tasks": Task.objects.filter(
                project__teams=user_team, is_completed=False
            ).count(),
            "count_unassigned_tasks": Task.objects.filter(
                project__teams=user_team, assignees__isnull=True,
            ).count(),
            "count_over_deadline_tasks": Task.objects.filter(
                project__teams=user_team, deadline__lt=datetime.date.today()
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


class TaskDetailView(generic.DetailView):
    model = Task
    comment_form = CommentForm
    assign_field_name = "assign_to_me"

    def get_context_data(self, **kwargs: Any) -> dict:
        context = super().get_context_data(**kwargs)
        context["comment_form"] = self.comment_form()
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseRedirect:

        task = Task.objects.get(pk=self.kwargs.get(self.pk_url_kwarg))

        comment_form = self.comment_form(request.POST)
        with transaction.atomic():
            if comment_form.is_valid():
                new_comment = comment_form.save(commit=False)
                new_comment.worker = request.user
                new_comment.task_id = self.kwargs.get(self.pk_url_kwarg)
                new_comment.save()

                Activity.objects.create(
                    type=Activity.ActivityTypeChoices.ADD_COMMENT,
                    task_id=self.kwargs.get(self.pk_url_kwarg),
                    worker=request.user
                )

        if self.assign_field_name in request.POST:
            with transaction.atomic():
                if request.user in task.assignees.all():
                    task.assignees.remove(request.user)
                else:
                    task.assignees.add(request.user)

                Activity.objects.create(
                    type=Activity.ActivityTypeChoices.UPDATE_TASK,
                    task_id=self.kwargs.get(self.pk_url_kwarg),
                    worker=request.user
                )

        return HttpResponseRedirect(
            redirect_to=reverse("task_manager:task_detail", args=[task.pk])
        )
