import datetime
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import QuerySet, Q
from django.forms import Form
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from task_manager.forms import (TaskFilterForm,
                                CommentForm,
                                TaskCreateForm,
                                TaskUpdateForm,
                                ProjectCreateForm,
                                ProjectUpdateForm,
                                TeamCreateForm,
                                TeamUpdateForm,
                                WorkerListFilter,
                                WorkerCreateForm,
                                WorkerUpdateForm,
                                PositionCreateForm,
                                TaskTypeCreateForm,
                                TagCreateForm,
                                NameExactFilterForm)
from task_manager.mixins import QuerysetFilterByUserMixin, TaskPermissionRequiredMixin
from task_manager.models import Task, Activity, Project, Team, Position, TaskType, Tag


class ListFilterView(generic.ListView):
    filter_form = None
    filter_context_name = "filter"
    name_paginate_parameter_for_session = "elems_on_page"

    def get_paginate_by(self, queryset: QuerySet) -> int:
        tasks_on_page = self.request.GET.get(self.name_paginate_parameter_for_session)
        if tasks_on_page and tasks_on_page.isdigit():
            self.request.session[self.name_paginate_parameter_for_session] = int(tasks_on_page)
        return self.request.session.get(self.name_paginate_parameter_for_session) or self.paginate_by

    def get_filter_form(self, *args: Any) -> Form:
        return self.filter_form(self.request.GET)

    def get_context_data(
            self,
            *,
            object_list: Optional[Any] = None,
            **kwargs: Any
    ) -> dict[str: Any]:
        context = super().get_context_data(object_list=object_list, **kwargs)

        if self.filter_form is not None:
            form = self.get_filter_form()
            context[self.filter_context_name] = form

        return context

    def get_filters(self) -> Q | None:

        if self.filter_form is not None:
            form = self.get_filter_form()

            if form.is_valid():
                filters = Q()
                for field, value in form.cleaned_data.items():
                    if value:
                        filters &= Q(**{field: value})
                return filters

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        filters = self.get_filters()

        if filters:
            return queryset.filter(filters)

        return queryset


class IndexView(LoginRequiredMixin, generic.TemplateView):
    number_of_last_tasks = 10
    number_of_last_activity = 10
    template_name = "task_manager/index.html"

    def get_context_data(self, **kwargs) -> dict[str: Any]:
        kwargs = super().get_context_data(**kwargs)
        user_tasks = Task.objects.filter_by_user(self.request.user)

        context = {
            "last_tasks": user_tasks.order_by(
                "-created_time"
            )[:self.number_of_last_tasks].prefetch_related("assignees"),
            "last_activity": Activity.objects.filter(task__in=user_tasks
                                                     ).order_by("-created_time")[:self.number_of_last_activity],
            "count_unfinished_tasks": user_tasks.filter(is_completed=False).count(),
            "count_unassigned_tasks": user_tasks.filter(assignees__isnull=True).count(),
            "count_over_deadline_tasks": user_tasks.filter(deadline__lt=datetime.date.today()).count()
        }

        kwargs.update(context)

        return kwargs


class TaskListFilterView(LoginRequiredMixin,
                         QuerysetFilterByUserMixin,
                         ListFilterView):
    model = Task
    paginate_by = settings.DEFAULT_PAGINATE_BY
    filter_form = TaskFilterForm

    def get_filter_form(self) -> TaskFilterForm:
        return self.filter_form(self.request.GET, user=self.request.user)


class TaskDetailView(LoginRequiredMixin,
                     TaskPermissionRequiredMixin,
                     generic.DetailView):
    model = Task
    comment_form = CommentForm
    assign_field_name = "assign_to_me"
    permission_required = "task_manager.view_task"

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


class TaskCreateView(LoginRequiredMixin,
                     generic.CreateView):
    model = Task
    form_class = TaskCreateForm

    def get_success_url(self) -> str:
        return reverse("task_manager:task_detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self) -> dict:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: TaskCreateForm) -> HttpResponseRedirect:
        with transaction.atomic():
            task = form.save()
            task.creator = self.request.user
            task.save()

            Activity.objects.create(
                type=Activity.ActivityTypeChoices.CREATE_TASK,
                task=task,
                worker=self.request.user
            )
            self.object = task

        return HttpResponseRedirect(self.get_success_url())


class TaskUpdateView(LoginRequiredMixin,
                     TaskPermissionRequiredMixin,
                     generic.UpdateView):
    model = Task
    form_class = TaskUpdateForm
    url_pattern_name = "task_manager:task_detail"
    permission_required = ("task_manager.view_task", "task_manager.change_task")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
        )

    def form_valid(self, form: TaskUpdateForm) -> HttpResponseRedirect:
        with transaction.atomic():
            task = form.save()

            self.object = task

            Activity.objects.create(
                type=Activity.ActivityTypeChoices.UPDATE_TASK,
                task=task,
                worker=self.request.user
            )

        return HttpResponseRedirect(self.get_success_url())


class TaskDeleteView(LoginRequiredMixin,
                     TaskPermissionRequiredMixin,
                     generic.DeleteView):
    model = Task
    success_url = reverse_lazy("task_manager:task_list")
    permission_required = ("task_manager.view_task", "task_manager.delete_task")


class ProjectListFilterView(LoginRequiredMixin,
                            QuerysetFilterByUserMixin,
                            ListFilterView):
    model = Project
    paginate_by = settings.DEFAULT_PAGINATE_BY
    filter_form = NameExactFilterForm


class ProjectDetailView(LoginRequiredMixin,
                        PermissionRequiredMixin,
                        generic.DetailView):
    model = Project
    permission_required = "task_manager.view_project"

    def has_permission(self) -> bool:
        if super().has_permission():
            return True

        project = get_object_or_404(
            self.model,
            **{self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
        )
        return project in self.request.user.team.projects.all()


class ProjectCreateView(PermissionRequiredMixin, generic.CreateView):
    model = Project
    form_class = ProjectCreateForm
    url_pattern_name = "task_manager:project_detail"
    permission_required = ("task_manager.view_project", "task_manager.add_project")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )


class ProjectUpdateView(PermissionRequiredMixin, generic.UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    url_pattern_name = "task_manager:project_detail"
    permission_required = ("task_manager.view_project", "task_manager.change_project")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )


class ProjectDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = Project
    success_url = reverse_lazy("task_manager:project_list")
    permission_required = ("task_manager.view_project", "task_manager.delete_project")


class TeamListFilterView(QuerysetFilterByUserMixin, ListFilterView):
    model = Team
    paginate_by = settings.DEFAULT_PAGINATE_BY
    filter_form = NameExactFilterForm
    queryset = Team.objects.exclude_default_team()


class TeamDetailView(PermissionRequiredMixin, generic.DetailView):
    model = Team
    permission_required = "task_manager.view_team"
    queryset = Team.objects.exclude_default_team()

    def has_permission(self) -> bool:
        if super().has_permission():
            return True

        team = get_object_or_404(
            self.model,
            **{self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
        )
        return team == self.request.user.team


class TeamCreateView(PermissionRequiredMixin, generic.CreateView):
    model = Team
    form_class = TeamCreateForm
    url_pattern_name = "task_manager:team_detail"
    permission_required = ("task_manager.view_team", "task_manager.add_team")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )

    def form_valid(self, form: TeamCreateForm) -> HttpResponseRedirect:
        team = form.save()

        if form.cleaned_data.get("projects"):
            team.projects.add(*form.cleaned_data.get("projects"))

        self.object = team

        return HttpResponseRedirect(self.get_success_url())


class TeamUpdateView(PermissionRequiredMixin, generic.UpdateView):
    model = Team
    form_class = TeamUpdateForm
    url_pattern_name = "task_manager:team_detail"
    permission_required = ("task_manager.view_team", "task_manager.change_team")
    queryset = Team.objects.exclude_default_team()

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )

    def get_initial(self) -> dict:
        initial_data = self.initial.copy()

        initial_data["projects"] = Project.objects.filter(teams=self.object)

        return initial_data

    def form_valid(self, form: TeamCreateForm) -> HttpResponseRedirect:
        team = form.save()
        if form.cleaned_data.get("projects"):
            team.projects.set(form.cleaned_data.get("projects"))

        self.object = team

        return HttpResponseRedirect(self.get_success_url())


class TeamDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = Team
    success_url = reverse_lazy("task_manager:team_list")
    permission_required = ("task_manager.view_team", "task_manager.delete_team")
    queryset = Team.objects.exclude_default_team()


class WorkerListFilterView(QuerysetFilterByUserMixin, ListFilterView):
    model = get_user_model()
    paginate_by = settings.DEFAULT_PAGINATE_BY
    filter_form = WorkerListFilter


class WorkerDetailView(PermissionRequiredMixin, generic.DetailView):
    model = get_user_model()
    permission_required = "task_manager.view_worker"

    def has_permission(self) -> bool:
        if super().has_permission():
            return True

        worker = get_object_or_404(
            self.model,
            **{self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
        )

        if self.model.objects.filter(pk=worker.pk).filter(
                team__projects__in=self.request.user.team.projects.all()
        ).exists():
            return True

        return False


class WorkerCreateView(PermissionRequiredMixin, generic.CreateView):
    model = get_user_model()
    form_class = WorkerCreateForm
    url_pattern_name = "task_manager:worker_detail"
    permission_required = ("task_manager.view_worker", "task_manager.add_worker")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )


class WorkerUpdateView(PermissionRequiredMixin, generic.UpdateView):
    model = get_user_model()
    form_class = WorkerUpdateForm
    url_pattern_name = "task_manager:worker_detail"
    permission_required = ("task_manager.view_worker", "task_manager.change_worker")

    def get_success_url(self) -> str:
        return reverse(
            self.url_pattern_name,
            kwargs={self.pk_url_kwarg: self.object.pk}
        )


class WorkerDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = get_user_model()
    success_url = reverse_lazy("task_manager:worker_list")
    permission_required = ("task_manager.view_worker", "task_manager.delete_worker")


class PositionListFilterView(ListFilterView):
    model = Position
    extra_context = {"form": PositionCreateForm}
    paginate_by = settings.DEFAULT_PAGINATE_BY
    filter_form = NameExactFilterForm


class PositionCreateView(PermissionRequiredMixin,
                         SuccessMessageMixin,
                         generic.CreateView):
    http_method_names = ["post"]
    model = Position
    form_class = PositionCreateForm
    success_url = reverse_lazy("task_manager:position_list")
    success_message = "Position create"
    permission_required = "task_manager.add_position"


class PositionDeleteView(PermissionRequiredMixin,
                         SuccessMessageMixin,
                         generic.DeleteView):
    http_method_names = ["post"]
    model = Position
    success_url = reverse_lazy("task_manager:position_list")
    success_message = "Position deleted "
    permission_required = "task_manager.delete_position"


class TaskTypeListFilterView(ListFilterView):
    model = TaskType
    paginate_by = settings.DEFAULT_PAGINATE_BY
    extra_context = {"form": TaskTypeCreateForm}
    filter_form = NameExactFilterForm


class TaskTypeCreateView(PermissionRequiredMixin,
                         SuccessMessageMixin,
                         generic.CreateView):
    http_method_names = ["post"]
    model = TaskType
    form_class = TaskTypeCreateForm
    success_url = reverse_lazy("task_manager:task_type_list")
    success_message = "Task type created"
    permission_required = "task_manager.add_tasktype"


class TaskTypeDeleteView(PermissionRequiredMixin,
                         SuccessMessageMixin,
                         generic.DeleteView):
    http_method_names = ["post"]
    model = TaskType
    success_url = reverse_lazy("task_manager:task_type_list")
    success_message = "Task type deleted"
    permission_required = "task_manager.delete_tasktype"


class TagListFilterView(ListFilterView):
    model = Tag
    paginate_by = settings.DEFAULT_PAGINATE_BY
    extra_context = {"form": TagCreateForm}
    filter_form = NameExactFilterForm


class TagCreateView(PermissionRequiredMixin,
                    SuccessMessageMixin,
                    generic.CreateView):
    http_method_names = ["post"]
    model = Tag
    form_class = TagCreateForm
    success_url = reverse_lazy("task_manager:tag_list")
    success_message = "Tag created"
    permission_required = "task_manager.add_tag"


class TagDeleteView(PermissionRequiredMixin,
                    SuccessMessageMixin,
                    generic.DeleteView):
    http_method_names = ["post"]
    model = Tag
    success_url = reverse_lazy("task_manager:tag_list")
    success_message = "Tag deleted"
    permission_required = "task_manager.delete_tag"
