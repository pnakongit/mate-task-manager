from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from task_manager.forms import TaskFilterForm, TaskCreateForm
from task_manager.models import Worker, Project, Team


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
