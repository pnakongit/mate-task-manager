from django.db.models import Manager, QuerySet


class TaskManager(Manager):

    def filter_by_user(self, user) -> QuerySet:
        queryset = self.get_queryset()
        return queryset.filter(project__teams__workers=user)


class ProjectManager(Manager):

    def filter_by_user(self, user) -> QuerySet:
        queryset = self.get_queryset()
        return queryset.filter(teams__workers=user)


class TeamManager(Manager):

    def filter_by_user(self, user) -> QuerySet:
        queryset = self.get_queryset()
        return queryset.filter(workers=user)
