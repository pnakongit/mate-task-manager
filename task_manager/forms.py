import datetime
from typing import Any

from django import forms
from django.conf import settings

from task_manager.models import Task, Worker, Comment, Tag, TaskType


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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("content",)
        labels = {
            "content": False,
        }
        widgets = {
            "content": forms.TextInput(attrs={"placeholder": "Add comment"})
        }


class TaskCreateForm(forms.ModelForm):
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=datetime.datetime.today()
    )
    task_type = forms.ModelChoiceField(
        widget=forms.Select,
        queryset=TaskType.objects.all(),
        empty_label=None
    )
    project = forms.ModelChoiceField(
        widget=forms.Select,
        queryset=None,
        empty_label=None
    )
    tags = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Task
        fields = (
            "name",
            "description",
            "deadline",
            "task_type",
            "priority",
            "project",
            "tags"
        )

    def __init__(self, *args: Any, user: settings.AUTH_USER_MODEL, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["project"].queryset = user.team.projects.all()
