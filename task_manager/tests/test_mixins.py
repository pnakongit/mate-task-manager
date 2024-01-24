from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from task_manager.mixins import QuerysetFilterByUserMixin
from task_manager.models import Team, Project


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
