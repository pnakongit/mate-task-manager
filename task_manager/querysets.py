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

        if user.team == self.model.get_default_team():
            return self.none()

        return self.filter(workers=user)


class WorkerQuerySet(QuerySet):

    def filter_by_user(self, user) -> QuerySet:
        from task_manager.models import Team
        if user.has_perm("task_manager.view_worker"):
            return self.all()

        exclude_team = Team.get_default_team()
        if user.team == exclude_team:
            return self.none()

        return self.filter(
            team__projects__in=user.team.projects.all()
        )
