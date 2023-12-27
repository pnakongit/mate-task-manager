from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404


class QuerysetFilterMixin:
    filter_parameter_name = None
    permission_parameter = None

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        user = self.request.user
        if not (user.is_superuser or user.has_perm(self.permission_parameter)):
            lookup_parameter = {self.filter_parameter_name: user}
            return queryset.filter(**lookup_parameter)
        return queryset


class TaskPermissionRequiredMixin(PermissionRequiredMixin):

    def has_permission(self) -> bool:
        perms = self.get_permission_required()

        if self.request.user.has_perms(perms):
            return True

        task = get_object_or_404(
            self.model,
            **{self.pk_url_kwarg: self.kwargs.get(self.pk_url_kwarg)}
        )

        return task.project in self.request.user.team.projects.all()
