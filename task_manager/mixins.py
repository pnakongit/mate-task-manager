from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404


class QuerysetFilterMixin:
    permission_parameter = None

    def get_queryset(self) -> QuerySet:
        user = self.request.user

        queryset = self.model.objects.all()

        if not user.has_perm(self.permission_parameter):
            queryset = self.model.objects.filter_by_user(user=user)

        filters = self.get_filters()

        if filters:
            return queryset.filter(filters)

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
