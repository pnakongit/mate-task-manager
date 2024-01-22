from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from task_manager.forms import (
    TaskFilterForm,
    TaskCreateForm,
    TaskUpdateForm,
    ProjectCreateForm,
    ProjectUpdateForm,
    TeamCreateForm,
    TeamUpdateForm, WorkerListFilter
)
from task_manager.models import Worker, Project, Team, Task


class BaseFormTestMixin:
    form_class = None
    necessary_fields = None
    required_fields = None
    optional_fields = None

    def setUp(self) -> None:
        self.form = self.form_class()

    def test_form_should_contain_necessary_fields(self) -> None:

        expected_necessary_fields = self.necessary_fields

        if expected_necessary_fields is None:
            expected_necessary_fields = set()

        self.assertEqual(
            set(self.form.fields.keys()),
            set(expected_necessary_fields),
        )

    def test_form_required_fields(self) -> None:

        expected_required_fields = self.required_fields

        if expected_required_fields is None:
            expected_required_fields = set()

        required_fields_in_form = {
            field_name
            for field_name, field_value in self.form.fields.items()
            if field_value.required
        }

        self.assertEqual(
            required_fields_in_form,
            set(expected_required_fields)
        )

    def test_form_optional_fields(self) -> None:

        expected_optional_fields = self.optional_fields

        if expected_optional_fields is None:
            expected_optional_fields = set()

        optional_fields_in_form = {
            field_name
            for field_name, field_value in self.form.fields.items()
            if not field_value.required
        }

        self.assertEqual(
            optional_fields_in_form,
            set(expected_optional_fields)
        )


class TaskFilterFormTest(TestCase):

    def setUp(self) -> None:
        self.worker = Worker.objects.create_user(
            username="test_username",
            email="test@test.com",
            password="123456"
        )

    def test_clean_assignees_field_value_not_none(self) -> None:
        request = RequestFactory().get(path="/?assignees=on")
        form = TaskFilterForm(request.GET, user=self.worker)

        form.is_valid()

        self.assertEqual(
            form.cleaned_data.get("assignees"),
            self.worker
        )

    def test_clean_assignees_field_value_none(self) -> None:
        request = RequestFactory().get(path="/")
        form = TaskFilterForm(request.GET, user=self.worker)

        form.is_valid()

        self.assertFalse(
            form.cleaned_data.get("assignees")
        )

    def test_project__in_filed_should_use_filter_by_user_queryset(self) -> None:
        team = Team.objects.create(name="Test team")
        team.workers.add(self.worker)
        team.save()

        project = Project.objects.create(name="Test project")
        project.teams.add(team)
        project.save()

        Project.objects.create(name="Test project without team and user")

        project_qs_by_user = Project.objects.filter_by_user(self.worker)

        with patch(f"{TaskFilterForm.__module__}.Project.objects.filter_by_user") as mock_filter_by_user:
            mock_filter_by_user.return_value = project_qs_by_user
            form = TaskFilterForm(user=self.worker)

        mock_filter_by_user.assert_called_once()
        self.assertQuerySetEqual(
            form.fields["project__in"].queryset,
            project_qs_by_user
        )


class TaskCreateFormTest(TestCase):

    def test_init_should_set_queryset_of_project_field_filtered_by_user(self) -> None:
        first_project = Project.objects.create(name="First project with user")
        second_project = Project.objects.create(name="Second project with user")
        Project.objects.create(name="Project without user")

        first_team = Team.objects.create(name="First team")
        first_team.projects.add(first_project)
        first_team.save()
        second_team = Team.objects.create(name="Second team")
        second_team.projects.add(second_project)
        second_team.save()

        get_user_model().objects.create_user(
            username="admin2",
            email="test@test.com",
            password="123456",
            team=second_team
        )
        worker = get_user_model().objects.create_user(
            username="admin",
            email="test@test.com",
            password="123456",
            team=first_team
        )

        form = TaskCreateForm(user=worker)

        self.assertEqual(
            list(form.fields["project"].queryset),
            [first_project]
        )


class TaskUpdateFormTest(TestCase):

    def setUp(self) -> None:
        project = Project.objects.create(
            name="Test project name"
        )
        team = Team.objects.create(
            name="First team",
        )
        team.projects.add(project)

        self.team = team

        self.task = Task.objects.create(
            name="Test task name",
            description="Test descriptions name",
            project=project
        )

        self.form = TaskUpdateForm(instance=self.task)

    def test_form_should_contain_necessary_fields(self) -> None:
        necessary_fields = {
            "name",
            "description",
            "deadline",
            "task_type",
            "priority",
            "tags",
            "is_completed",
            "assignees"
        }
        self.assertEqual(
            set(self.form.fields.keys()),
            necessary_fields
        )

    def test_all_fields_should_be_required(self) -> None:
        for field_value in self.form.fields.values():
            self.assertTrue(field_value.required)

    def test_assignees_field_can_select_workers_from_teams_of_task_project(self) -> None:
        Worker.create_workers(count=3)
        Worker.create_workers(count=2, team=self.team)
        form = TaskUpdateForm(instance=self.task)

        expected_qs_of_assignees_field = Worker.objects.filter(
            team__projects__tasks=self.task
        )

        self.assertQuerySetEqual(
            form.fields["assignees"].queryset,
            expected_qs_of_assignees_field,
            ordered=False
        )


class ProjectCreateFormTest(TestCase):
    def setUp(self) -> None:
        self.form = ProjectCreateForm()

    def test_form_should_contain_necessary_fields(self) -> None:
        necessary_fields = {
            "name", "description", "teams"
        }

        self.assertEqual(
            set(self.form.fields.keys()),
            necessary_fields
        )

    def test_required_fields(self) -> None:
        expected_required_fields = {
            "name", "description"
        }

        required_fields_in_form = {
            field_name
            for field_name, field_value in self.form.fields.items()
            if field_value.required
        }

        self.assertEqual(
            required_fields_in_form,
            expected_required_fields
        )

    def test_optional_fields(self) -> None:
        expected_optional_fields = {"teams"}

        optional_fields_in_form = {
            field_name
            for field_name, field_value in self.form.fields.items()
            if not field_value.required
        }

        self.assertEqual(
            optional_fields_in_form,
            expected_optional_fields
        )

    def test_default_team_not_available_in_teams_field(self) -> None:
        default_team = Team.get_default_team()

        Team.objects.create(name="Test team name in method")
        Team.objects.create(name="Test team name in method second")

        expected_queryset = Team.objects.exclude(pk=default_team.pk)

        self.assertQuerySetEqual(
            self.form.fields["teams"].queryset,
            expected_queryset,
            ordered=False
        )


class ProjectUpdateFormTest(TestCase):

    def test_should_inherit_from_projectcreateform(self) -> None:
        self.assertTrue(
            issubclass(ProjectUpdateForm, ProjectCreateForm)
        )


class TeamCreateFormTest(BaseFormTestMixin, TestCase):
    form_class = TeamCreateForm
    necessary_fields = ("name", "projects")
    required_fields = ("name",)
    optional_fields = ("projects",)


class TeamUpdateFormTest(TestCase):

    def test_should_inherit_from_teamcreateform(self) -> None:
        self.assertTrue(
            issubclass(TeamUpdateForm, TeamCreateForm)
        )


class WorkerListFilterTest(BaseFormTestMixin, TestCase):
    form_class = WorkerListFilter
    necessary_fields = ("username__icontains", "email")
    optional_fields = ("username__icontains", "email")
