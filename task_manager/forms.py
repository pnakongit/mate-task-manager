import datetime
from typing import Any

from django import forms
from django.conf import settings

from task_manager.models import Task, Worker, Comment, Tag, TaskType, Project, Team


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


class TaskUpdateForm(forms.ModelForm):
    deadline = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=datetime.datetime.today()
    )
    task_type = forms.ModelChoiceField(
        widget=forms.Select,
        queryset=TaskType.objects.all(),
        empty_label=None
    )
    tags = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Tag.objects.all(),
    )
    is_completed = forms.ChoiceField(
        choices=((True, "Yes"), (False, "Not"))
    )
    assignees = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=None
    )

    class Meta:
        model = Task
        fields = (
            "name",
            "description",
            "deadline",
            "task_type",
            "priority",
            "tags",
            "is_completed",
            "assignees"
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["assignees"].queryset = Worker.objects.filter(team__projects__tasks=self.instance.pk)


class ProjectCreateForm(forms.ModelForm):
    teams = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Team.objects.all(),
        required=False
    )

    class Meta:
        model = Project
        fields = ("name", "description", "teams")


class ProjectUpdateForm(ProjectCreateForm):
    pass


class TeamCreateForm(forms.ModelForm):
    projects = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Project.objects.all(),
        required=False
    )

    class Meta:
        model = Team
        fields = ("name",)
