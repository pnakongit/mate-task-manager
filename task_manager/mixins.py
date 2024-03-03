from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.http import HttpResponseRedirect


class QuerysetFilterByUserMixin:

    def get_queryset(self) -> QuerySet:
        user = self.request.user

        queryset = super().get_queryset()

        return queryset.filter_by_user(user)


class ExcludeDefaultTeamMixin:

    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        return qs.exclude_default_team()


class TaskPermissionRequiredMixin(PermissionRequiredMixin):

    def has_permission(self) -> bool:
        perms = self.get_permission_required()

        if self.request.user.has_perms(perms):
            return True

        try:
            task = self.model.objects.get(
                **{self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
            )
        except self.model.DoesNotExist:
            return False

        return task.project in self.request.user.team.projects.all()


class RedirectInvalidFormMixin:
    fail_url = None

    def get_fail_url(self) -> None:
        if self.fail_url is None:
            raise ImproperlyConfigured(
                "Please provide a fail url"
            )
        return self.fail_url

    def form_invalid(self, *args: Any, **kwargs: Any) -> HttpResponseRedirect:
        return HttpResponseRedirect(self.get_fail_url())
