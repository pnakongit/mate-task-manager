from typing import Any

from django import forms
from django.conf import settings

from task_manager.models import Task, Worker


class TaskFilterForm(forms.Form):
    assignees = forms.BooleanField(
        label="Assigned to me",
        required=False,
    )
    assignees__isnull = forms.BooleanField(
        label="Show unassigned",
        required=False,
    )
    is_completed = forms.ChoiceField(
        label="Completion status:",
        choices=((None, "All"),
                 (True, "Completed"),
                 (False, "Uncompleted")),
        required=False
    )
    tags__name = forms.CharField(
        label="Search by tag:",
        required=False,
        max_length=255
    )
    deadline__gt = forms.DateField(
        label="Date from:",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False
    )
    deadline__lt = forms.DateField(
        label="Date until:",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False
    )
    priority__in = forms.MultipleChoiceField(
        label="Priority:",
        widget=forms.CheckboxSelectMultiple,
        choices=Task.PriorityChoices.choices,
        required=False
    )
    project__in = forms.ModelMultipleChoiceField(
        label="Project:",
        widget=forms.CheckboxSelectMultiple,
        queryset=None,
        required=False,
    )

    def __init__(self, *args: Any, user: settings.AUTH_USER_MODEL, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["project__in"].queryset = user.team.projects.all()

    def clean_assignees(self) -> Worker:
        assignees = self.cleaned_data.get("assignees")
        if assignees:
            assignees = self.user
        return assignees
