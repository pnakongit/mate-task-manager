from django.db.models import QuerySet


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
