from django.db.models import QuerySet


class TaskQuerySet(QuerySet):
    def filter_by_user(self, user) -> QuerySet:
        if user.has_perm("task_manager.view_task"):
            return self.all()

        return self.filter(project__teams__workers=user)


class ProjectQuerySet(QuerySet):

    def filter_by_user(self, user) -> QuerySet:
        if user.has_perm("task_manager.view_project"):
            return self.all()
        return self.filter(teams__workers=user)


class TeamQuerySet(QuerySet):

    def filter_by_user(self, user) -> QuerySet:
        if user.has_perm("task_manager.view_team"):
            return self.all()
        return self.filter(workers=user)


class WorkerQuerySet(QuerySet):

    def filter_by_user(self, user) -> QuerySet:
        if user.has_perm("task_manager.view_worker"):
            return self.all()

        user_projects = user.team.projects.all() if user.team else []

        return self.filter(team__projects__in=user_projects)
