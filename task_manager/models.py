from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class NameInfo(models.Model):
    name = models.CharField(max_length=65, unique=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name


class Team(NameInfo):
    pass


class Position(NameInfo):
    pass


class Tag(NameInfo):
    pass


class TaskType(NameInfo):
    pass


class Worker(AbstractUser):
    position = models.ForeignKey(to=Position, related_name="workers", null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(to=Team, related_name="workers", null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Project(models.Model):
    name = models.CharField(max_length=65)
    description = models.CharField(max_length=255)
    teams = models.ManyToManyField(to=Team, related_name="teams")


class Task(models.Model):
    class PriorityChoices(models.IntegerChoices):
        LOW = 1, "Low"
        NORMAL = 2, "Normal"
        HIGH = 3, "High"
        BLOCK = 4, "Block"

    name = models.CharField(max_length=65)
    description = models.CharField(max_length=255)
    deadline = models.DateField()
    task_type = models.ForeignKey(
        to=TaskType,
        null=True,
        on_delete=models.SET_NULL,
        related_name="tasks"
    )
    is_completed = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(
        choices=PriorityChoices.choices,
        default=PriorityChoices.LOW
    )
    creator = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks"
    )
    assignees = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        related_name="assigned_tasks"
    )
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(to=Tag, related_name="tasks")

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="name_idx"),
            models.Index(fields=["description"], name="description_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.pk} {self.name}"


class Comment(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    content = models.CharField(max_length=255)
    task = models.ForeignKey(
        to=Task,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    worker = models.ForeignKey(
        to=Worker,
        on_delete=models.CASCADE,
        related_name="comments"
    )


class Activity(models.Model):
    class ActivityTypeChoices(models.IntegerChoices):
        CREATE_TASK = 1, "Create task"
        UPDATE_TASK = 2, "Update task"
        ADD_COMMENT = 3, "Add comment"
        ASSIGN_TASK = 4, "Assign task"
        CHANGE_STATUS = 5, "Change task status"

    type = models.PositiveIntegerField(choices=ActivityTypeChoices)
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE, related_name="activity")
