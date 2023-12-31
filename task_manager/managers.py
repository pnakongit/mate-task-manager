from django.db.models import Manager, QuerySet


class TaskManager(Manager):

    def filter_by_user(self, user) -> QuerySet:
        queryset = self.get_queryset()
        return queryset.filter(project__teams__workers=user)
