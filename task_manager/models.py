from django.contrib.auth.models import AbstractUser
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=65, unique=True)


class Position(models.Model):
    name = models.CharField(max_length=65, unique=True)

    def __str__(self) -> str:
        return self.name


class Worker(AbstractUser):
    position = models.ForeignKey(to=Position, related_name="workers", null=True, on_delete=models.SET_NULL)
    team = models.ForeignKey(to=Team, related_name="workers", null=True, on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Tag(models.Model):
    name = models.CharField(max_length=65, unique=True)

    def __str__(self) -> str:
        return self.name


class TaskType(models.Model):
    name = models.CharField(max_length=65, unique=True)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=65)
    description = models.CharField(max_length=255)
    teams = models.ManyToManyField(to=Team, related_name="teams")
