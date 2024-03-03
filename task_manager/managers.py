from django.contrib.auth.models import UserManager

from task_manager.querysets import WorkerQuerySet


class WorkerManager(UserManager.from_queryset(WorkerQuerySet)):
    pass
