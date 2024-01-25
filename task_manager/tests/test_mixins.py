from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, RequestFactory

from task_manager.mixins import QuerysetFilterByUserMixin, TaskPermissionRequiredMixin
from task_manager.models import Team, Project, Task


class QuerysetFilterByUserMixinTest(TestCase):

    def setUp(self) -> None:
        project = Project.objects.create(name="First test project")
        team = Team.objects.create(name="First test team")
        team.projects.add(project)

        self.worker = get_user_model().objects.create_user(
            username="test user",
            password="1234567",
            email="test@test.com",
            first_name="Test first_name",
            last_name="Test last_name",
            team=team
        )

        request_obj = RequestFactory().request()
        request_obj.user = self.worker

        mixin_obj = QuerysetFilterByUserMixin()
        mixin_obj.request = request_obj
        self.mixin_obj = mixin_obj

    def test_get_queryset_should_return_filtered_by_user_qs(self) -> None:
        request_user_team = self.mixin_obj.request.user.team
        get_user_model().create_workers(
            count=3,
            team=request_user_team
        )

        second_project = Project.objects.create(name="New project")
        second_team = Team.objects.create(name="New team")
        second_team.projects.add(second_project)

        get_user_model().create_workers(
            count=3,
            team=second_team
        )

        get_user_model().create_workers(
            count=3
        )

        all_workers_qs = get_user_model().objects.all()

        with patch(f"{QuerysetFilterByUserMixin.__module__}.super") as mock_super:
            mock_super.return_value.get_queryset.return_value = all_workers_qs
            returned_qs = self.mixin_obj.get_queryset()

        expected_qs = get_user_model().objects.filter(
            team__projects__in=self.worker.team.projects.all()
        )

        self.assertQuerySetEqual(returned_qs, expected_qs, ordered=False)

    def test_get_queryset_should_use_filter_by_user_method(self) -> None:
        all_workers_qs = get_user_model().objects.all()

        with (
            patch(f"{QuerysetFilterByUserMixin.__module__}.super") as mock_super,
            patch.object(all_workers_qs, "filter_by_user") as mock_filter_by_user
        ):
            mock_super.return_value.get_queryset.return_value = all_workers_qs
            self.mixin_obj.get_queryset()

        mock_filter_by_user.assert_called_once()


class TaskPermissionRequiredMixinTest(TestCase):

    def setUp(self) -> None:
        project = Project.objects.create(
            name="Test project name"
        )
        team = Team.objects.create(
            name="Test team name"
        )
        team.projects.add(project)
        self.task = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=project
        )
        user = get_user_model().objects.create_user(
            username="test_admin",
            password="123456",
            email="test@test.com",
            first_name="Test first name",
            last_name="Test last name",
        )
        request = RequestFactory().request()
        request.user = user

        mixin_obj = TaskPermissionRequiredMixin()
        mixin_obj.model = Task
        mixin_obj.pk_url_kwarg = "pk"
        mixin_obj.kwargs = {"pk": self.task.pk}
        mixin_obj.permission_required = "task_manager.view_task"
        mixin_obj.request = request
        self.mixin_obj = mixin_obj

    def test_has_permission_return_true_if_user_is_superuser(self) -> None:
        mixin_obj = self.mixin_obj

        super_user = get_user_model().objects.create_superuser(
            username="superuser_admin",
            password="123456",
            email="testsuoeradmin@test.com",
            first_name="Test first name",
            last_name="Test last name"
        )

        mixin_obj.request.user = super_user

        self.assertTrue(mixin_obj.has_permission())

    def test_has_permission_return_true_if_user_has_permission(self) -> None:
        mixin_obj = self.mixin_obj

        user = mixin_obj.request.user
        permission = Permission.objects.get(codename="view_task")
        user.user_permissions.add(permission)

        self.assertTrue(mixin_obj.has_permission())

    def test_has_permission_return_true_if_user_in_team_of_task_project(self) -> None:
        mixin_obj = self.mixin_obj
        team_of_task_project = self.task.project.teams.first()

        user = mixin_obj.request.user
        user.team = team_of_task_project
        user.save()

        self.assertFalse(user.get_all_permissions())

        self.assertTrue(self.mixin_obj.has_permission())

    def test_has_permission_return_false_if_user_not_in_team_of_task_project(self) -> None:
        mixin_obj = self.mixin_obj
        team_of_task_project = self.task.project.teams.first()

        second_project = Project.objects.create(
            name="Test second project"
        )
        second_team = Team.objects.create(
            name="Test second team"
        )
        second_team.projects.add(second_project)

        user = mixin_obj.request.user
        user.team = second_team
        user.save()

        self.assertFalse(user.get_all_permissions())
        self.assertNotEqual(team_of_task_project, second_team)

        self.assertFalse(self.mixin_obj.has_permission())

    def test_has_permission_return_false_if_obj_not_exist_and_user_doesnt_has_perms(self) -> None:
        mixin_obj = self.mixin_obj
        user = mixin_obj.request.user

        self.assertFalse(user.get_all_permissions())

        last_task_pk = Task.objects.last().pk
        self.mixin_obj.kwargs = {"pk": last_task_pk + 1}

        self.assertFalse(self.mixin_obj.has_permission())

    def test_has_permission_return_true_if_obj_not_exist_and_user_has_perms(self) -> None:
        mixin_obj = self.mixin_obj
        user = mixin_obj.request.user

        permission = Permission.objects.get(codename="view_task")
        user.user_permissions.add(permission)

        last_task_pk = Task.objects.last().pk
        self.mixin_obj.kwargs = {"pk": last_task_pk + 1}

        self.assertTrue(self.mixin_obj.has_permission())
