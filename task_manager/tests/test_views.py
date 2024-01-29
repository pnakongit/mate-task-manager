import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Q
from django.test import TestCase, RequestFactory
from django.urls import reverse

from task_manager.forms import WorkerListFilter, TaskFilterForm
from task_manager.mixins import QuerysetFilterByUserMixin
from task_manager.models import Worker, Task, Project, Team, Activity
from task_manager.views import ListFilterView, IndexView, TaskListFilterView


class ListFilterViewTest(TestCase):

    def setUp(self) -> None:
        self.factory = RequestFactory()
        view = ListFilterView()
        view.model = Worker
        view.paginate_by = settings.DEFAULT_PAGINATE_BY
        view.filter_form = WorkerListFilter
        self.view = view

        self.user = get_user_model().objects.create_user(
            username="test_username",
            email="test@test.com",
            password="1234567",
            first_name="Test first name",
            last_name="Test last name"
        )

    def test_default_value_of_filter_context_name_attribute(self) -> None:
        expected_name = "filter"

        self.assertEqual(
            ListFilterView.filter_context_name,
            expected_name
        )

    def test_default_value_of_name_paginate_parameter_for_session_attribute(self) -> None:
        expected_name = "elems_on_page"

        self.assertEqual(
            ListFilterView.name_paginate_parameter_for_session,
            expected_name
        )

    def test_get_paginate_by_should_return_value_default_value_if_it_not_in_session(self) -> None:
        request = self.factory.get("/")

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        queryset = self.view.get_queryset()
        self.assertEqual(
            self.view.get_paginate_by(queryset),
            settings.DEFAULT_PAGINATE_BY
        )

    def test_get_paginate_by_should_set_value_to_session_if_int_value(self) -> None:
        elems_on_page = 15
        request = self.factory.get(
            f"/?{self.view.name_paginate_parameter_for_session}={elems_on_page}"
        )

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        queryset = self.view.get_queryset()
        self.view.get_paginate_by(queryset)

        self.assertEqual(
            self.view.request.session.get(self.view.name_paginate_parameter_for_session),
            elems_on_page
        )

    def test_get_paginate_by_should_transform_str_digit_value_and_set_to_session(self) -> None:
        elems_on_page = "15"
        request = self.factory.get(
            f"/?{self.view.name_paginate_parameter_for_session}={elems_on_page}"
        )

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        queryset = self.view.get_queryset()
        self.view.get_paginate_by(queryset)

        self.assertEqual(
            self.view.request.session.get(self.view.name_paginate_parameter_for_session),
            int(elems_on_page)
        )

    def test_get_paginate_by_should_ignore_set_to_session_if_value_not_valid(self) -> None:
        elems_on_page = "abc"
        request = self.factory.get(
            f"/?{self.view.name_paginate_parameter_for_session}={elems_on_page}"
        )

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        queryset = self.view.get_queryset()
        self.view.get_paginate_by(queryset)

        self.assertIsNone(
            self.view.request.session.get(self.view.name_paginate_parameter_for_session)
        )

    def test_get_paginate_by_should_return_value_from_session_if_it_exist(self) -> None:
        elems_on_page = 10
        request = self.factory.get(
            f"/?{self.view.name_paginate_parameter_for_session}={elems_on_page}"
        )

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        request.session[self.view.name_paginate_parameter_for_session] = elems_on_page

        queryset = self.view.get_queryset()
        self.view.get_paginate_by(queryset)

        self.assertEqual(
            self.view.get_paginate_by(queryset),
            elems_on_page
        )

    def test_get_filter_form_return_form_instance(self) -> None:
        request = self.factory.get("/")

        request.user = self.user
        self.view.setup(request)

        self.assertIsInstance(
            self.view.get_filter_form(),
            self.view.filter_form
        )

    def test_get_context_data_should_add_form_to_context_if_form_exist(self) -> None:
        request = self.factory.get("/")

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        object_list = self.view.get_queryset()
        context = self.view.get_context_data(object_list=object_list)

        self.assertIsInstance(
            context.get(ListFilterView.filter_context_name),
            self.view.filter_form
        )

    def test_get_context_data_not_add_form_to_context_if_form_is_none(self) -> None:
        self.view.filter_form = None

        request = self.factory.get("/")

        request.user = self.user
        self.view.setup(request)

        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()

        object_list = self.view.get_queryset()
        context = self.view.get_context_data(object_list=object_list)

        self.assertIsNone(
            context.get(ListFilterView.filter_context_name),
        )

    def test_get_filters_should_return_q_object_if_form_specified_and_valid(self) -> None:
        request = self.factory.get("/?username__icontains=test")

        request.user = self.user
        self.view.setup(request)

        self.assertEqual(
            self.view.get_filters(),
            Q(username__icontains="test")
        )

    def test_get_filters_should_return_none_if_form_is_not_specified(self) -> None:
        self.view.filter_form = None
        request = self.factory.get("/?username__icontains=test")

        request.user = self.user
        self.view.setup(request)

        self.assertIsNone(
            self.view.get_filters()
        )

    def test_get_queryset_should_return_filtered_qs_if_filters_exist(self) -> None:
        get_user_model().create_workers(count=3)

        request = self.factory.get(f"/?username__icontains={self.user.username}")

        request.user = self.user
        self.view.setup(request)

        view_filters = self.view.get_filters()
        self.assertTrue(view_filters)

        expected_qs = get_user_model().objects.filter(view_filters)

        self.assertQuerySetEqual(
            self.view.get_queryset(),
            expected_qs
        )

    def test_get_queryset_should_return_unfiltered_qs_if_filters_does_not_exist(self) -> None:
        get_user_model().create_workers(count=3)

        request = self.factory.get("/")

        request.user = self.user
        self.view.setup(request)

        expected_qs = get_user_model().objects.all()

        self.assertQuerySetEqual(
            self.view.get_queryset(),
            expected_qs,
            ordered=False
        )


class IndexViewTest(TestCase):
    url = reverse("task_manager:index")

    def setUp(self) -> None:
        self.project_with_user = Project.objects.create(
            name="First project name"
        )
        user_team = Team.objects.create(
            name="Test team name"
        )
        user_team.projects.add(self.project_with_user)

        self.user = get_user_model().objects.create_user(
            username="test_admin",
            password="1234567",
            team=user_team
        )

        Task.create_tasks(count=15, project=self.project_with_user)

        self.project_without_user = Project.objects.create(
            name="Second project name"
        )
        Task.create_tasks(count=15, project=self.project_without_user)

        self.client.force_login(self.user)

    def test_number_of_last_tasks_value(self) -> None:
        expected_value = 10

        self.assertEqual(
            IndexView.number_of_last_tasks,
            expected_value
        )

    def test_number_of_last_activity_value(self) -> None:
        expected_value = 10

        self.assertEqual(
            IndexView.number_of_last_activity,
            expected_value
        )

    def test_index_view_login_required(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_context_should_has_user_last_tasks_qs(self) -> None:
        response = self.client.get(self.url)

        user_task = Task.objects.filter_by_user(self.user)
        expected_qs = user_task.order_by(
            "-created_time"
        )[:IndexView.number_of_last_tasks]

        self.assertQuerySetEqual(
            response.context["last_tasks"],
            expected_qs
        )

    def test_context_should_has_user_last_activity_qs(self) -> None:
        user_tasks = Task.objects.filter_by_user(self.user)

        for task in user_tasks:
            Activity.objects.create(
                task=task,
                worker=self.user,
                type=Activity.ActivityTypeChoices.UPDATE_TASK
            )

        response = self.client.get(self.url)

        expected_qs = Activity.objects.filter(
            task__in=user_tasks
        ).order_by("-created_time")[:IndexView.number_of_last_activity]

        self.assertQuerySetEqual(
            response.context["last_activity"],
            expected_qs
        )

    def test_context_should_has_count_unfinished_tasks(self) -> None:
        Task.create_tasks(
            count=15,
            project=self.project_with_user,
            is_completed=True
        )
        Task.create_tasks(
            count=15,
            project=self.project_with_user,
            is_completed=True
        )

        response = self.client.get(self.url)

        user_tasks = Task.objects.filter_by_user(self.user)
        expected_value = user_tasks.filter(is_completed=False).count()

        self.assertEqual(
            response.context["count_unfinished_tasks"],
            expected_value
        )

    def test_context_should_has_count_unassigned_tasks(self) -> None:
        Task.create_tasks(
            count=15,
            project=self.project_with_user,
            assignees=[self.user]
        )

        response = self.client.get(self.url)

        user_tasks = Task.objects.filter_by_user(self.user)
        expected_value = user_tasks.filter(assignees__isnull=True).count()

        self.assertEqual(
            response.context["count_unassigned_tasks"],
            expected_value
        )

    def test_context_should_has_count_over_deadline_tasks(self) -> None:
        expired_date = (datetime.date.today() - datetime.timedelta(days=3))

        Task.create_tasks(
            count=15,
            project=self.project_with_user,
            deadline=expired_date.isoformat()
        )

        Task.create_tasks(
            count=15,
            project=self.project_without_user,
            deadline=expired_date.isoformat()
        )

        response = self.client.get(self.url)

        user_tasks = Task.objects.filter_by_user(self.user)
        expected_value = user_tasks.filter(
            deadline__lt=datetime.date.today()
        ).count()

        self.assertEqual(
            response.context["count_over_deadline_tasks"],
            expected_value
        )

    def test_should_use_correct_template(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "task_manager/index.html")


class TaskListFilterViewTest(TestCase):
    url = reverse("task_manager:task_list")

    def setUp(self) -> None:
        self.project_with_user = Project.objects.create(
            name="Project with user"
        )
        team = Team.objects.create(name="Team with user")
        team.projects.add(self.project_with_user)
        self.user = get_user_model().objects.create_user(
            username="admin_test",
            password="1234567",
            team=team
        )
        Task.create_tasks(
            project=self.project_with_user,
            count=2
        )

        self.client.force_login(self.user)

    def test_task_list_filter_login_required(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_task_list_filter_paginated_by_value(self) -> None:
        self.assertEqual(
            TaskListFilterView.paginate_by,
            settings.DEFAULT_PAGINATE_BY
        )

    def test_task_list_filter_paginated(self) -> None:
        paginated_by = TaskListFilterView.paginate_by
        num_user_tasks = Task.objects.filter_by_user(self.user).count()

        if paginated_by >= num_user_tasks:
            num_additional_tasks = paginated_by - num_user_tasks + 1
            Task.create_tasks(
                count=num_additional_tasks,
                project=self.project_with_user
            )

        expected_qs = Task.objects.filter_by_user(self.user)[:paginated_by]

        response = self.client.get(self.url)
        self.assertQuerySetEqual(
            response.context["task_list"],
            expected_qs,
            ordered=False
        )

    def test_get_filter_form_return_form_instance(self) -> None:
        response = self.client.get(self.url)

        self.assertIsInstance(
            response.context["view"].get_filter_form(),
            TaskListFilterView.filter_form
        )

    def test_task_list_filter_filtered(self) -> None:

        Task.create_tasks(
            project=self.project_with_user,
            count=2,
            priority=Task.PriorityChoices.HIGH
        )

        response = self.client.get(self.url, data={"priority__in": 3})

        expected_qs = Task.objects.filter_by_user(self.user).filter(priority__in=[3, ])

        paginate_by = TaskListFilterView.paginate_by
        if expected_qs.count() > paginate_by:
            expected_qs = expected_qs[:paginate_by]

        self.assertQuerySetEqual(
            response.context["task_list"],
            expected_qs,
            ordered=False
        )

    def test_task_list_should_contain_only_available_for_user_tasks(self) -> None:

        Task.create_tasks(
            project=Project.objects.create(name="Project without user"),
            count=2
        )

        response = self.client.get(self.url)

        expected_qs = Task.objects.filter_by_user(self.user)

        paginate_by = TaskListFilterView.paginate_by
        if expected_qs.count() > paginate_by:
            expected_qs = expected_qs[:paginate_by]

        self.assertQuerySetEqual(
            response.context["task_list"],
            expected_qs,
            ordered=False
        )

    def test_should_user_qet_queryset_method_from_querysetfilterbyusermixin(self) -> None:

        with patch(f"{QuerysetFilterByUserMixin.__module__}."
                   "QuerysetFilterByUserMixin.get_queryset") as mock_method:
            mock_method.return_value = Task.objects.filter_by_user(self.user)
            self.client.get(self.url)

            mock_method.assert_called()
