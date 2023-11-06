from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=65, unique=True)


class Position(models.Model):
    name = models.CharField(max_length=65, unique=True)

    def __str__(self) -> str:
        return self.name
