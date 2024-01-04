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
