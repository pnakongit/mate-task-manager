from __future__ import annotations

import datetime
from typing import Optional, Iterable

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from faker import Faker

from task_manager.managers import WorkerManager
from task_manager.querysets import TaskQuerySet, ProjectQuerySet, TeamQuerySet
from task_manager.utils import get_next_three_days_date


class NameInfo(models.Model):
    name = models.CharField(max_length=65, unique=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Team(NameInfo):
    objects = TeamQuerySet.as_manager()

    @classmethod
    def get_default_team(cls) -> Team:
        team, _ = cls.objects.get_or_create(
            name="No team"
        )
        return team

    @classmethod
    def get_exclude_team(cls) -> Q:
        return ~Q(pk=cls.get_default_team().pk)


class Position(NameInfo):
    pass


class Tag(NameInfo):
    pass


class TaskType(NameInfo):
    pass


class Worker(AbstractUser):
    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    position = models.ForeignKey(
        to=Position,
        related_name="workers",
        blank=True, null=True,
        on_delete=models.SET_NULL
    )
    team = models.ForeignKey(
        to=Team,
        related_name="workers",
        null=True,
        on_delete=models.SET(Team.get_default_team),
        default=None
    )

    objects = WorkerManager()

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        verbose_name = "Worker"
        verbose_name_plural = "Workers"
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs) -> None:
        if self.team is None:
            self.team = Team.get_default_team()

        super().save(*args, **kwargs)

    @classmethod
    def create_workers(
            cls,
            count: int = 1,
            team: Optional[Team] = None,
            position: Optional[Position] = None
    ) -> list[Worker]:
        faker = Faker()
        email_domain = "test-faker.test"
        test_password = "123456"

        bulk_list = []
        if not team:
            team = Team.get_default_team()

        for _ in range(count):
            obj = cls(
                username=faker.user_name(),
                email=faker.email(domain=email_domain),
                first_name=faker.first_name(),
                last_name=faker.last_name(),
                position=position,
                team=team
            )
            obj.set_password(test_password)
            bulk_list.append(obj)

        return cls.objects.bulk_create(bulk_list)


class Project(models.Model):
    name = models.CharField(max_length=65)
    description = models.CharField(max_length=255)
    teams = models.ManyToManyField(
        to=Team,
        related_name="projects",
        limit_choices_to=Team.get_exclude_team
    )

    objects = ProjectQuerySet.as_manager()

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    class PriorityChoices(models.IntegerChoices):
        LOW = 1, "Low"
        NORMAL = 2, "Normal"
        HIGH = 3, "High"
        BLOCK = 4, "Block"

    name = models.CharField(max_length=65)
    description = models.TextField()
    deadline = models.DateField(
        default=get_next_three_days_date,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(
                limit_value=datetime.date.today,
                message="Ensure date is greater than or equal to %(limit_value)s."
            )
        ]
    )
    task_type = models.ForeignKey(
        to=TaskType,
        blank=True,
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
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks"
    )
    assignees = models.ManyToManyField(
        to=settings.AUTH_USER_MODEL,
        related_name="assigned_tasks",
        blank=True
    )
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(
        to=Tag,
        related_name="tasks",
        blank=True
    )

    objects = TaskQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["name"], name="name_idx"),
            models.Index(fields=["description"], name="description_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.pk} {self.name}"

    @classmethod
    def create_tasks(
            cls,
            *,
            project: Project,
            count: int = 1,
            priority: int = PriorityChoices.LOW,
            is_completed: bool = False,
            deadline: str = None,
            task_type: Optional[TaskType] = None,
            creator: Optional[Worker] = None,
            tags: Optional[Iterable[Tag]] = None,
            assignees: Optional[Iterable[Worker]] = None,
    ) -> list[Task]:
        fake = Faker()
        bulk_list = []

        for _ in range(count):
            obj = cls(
                name=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                task_type=task_type,
                is_completed=is_completed,
                priority=priority,
                creator=creator,
                project=project,
            )
            if deadline is not None:
                obj.deadline = deadline
            bulk_list.append(obj)
        task_list = cls.objects.bulk_create(bulk_list)

        if tags is not None:
            for tag in tags:
                tag.tasks.add(*task_list)

        if assignees is not None:
            for assignee in assignees:
                assignee.assigned_tasks.add(*task_list)

        return task_list


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

    def __str__(self) -> str:
        return f"Comment {self.pk}"


class Activity(models.Model):
    class ActivityTypeChoices(models.IntegerChoices):
        CREATE_TASK = 1, "created task"
        UPDATE_TASK = 2, "updated task"
        ADD_COMMENT = 3, "commented task"

    type = models.PositiveIntegerField(choices=ActivityTypeChoices.choices)
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE, related_name="activities")
    worker = models.ForeignKey(to=Worker, on_delete=models.CASCADE, related_name="activities")
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "created_time"

    def __str__(self) -> str:
        return f"Activity {self.pk}"
