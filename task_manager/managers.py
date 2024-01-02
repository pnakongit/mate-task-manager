from django.contrib.auth.models import UserManager
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


class WorkerManager(UserManager):

    def filter_by_user(self, user) -> QuerySet:
        user_projects = user.team.projects.all() if user.team else []
        queryset = self.get_queryset()
        return queryset.filter(team__projects__in=user_projects)
