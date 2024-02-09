import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.sessions.middleware import SessionMiddleware
from django.db.models import Q
from django.test import TestCase, RequestFactory
from django.urls import reverse
from faker import Faker

from task_manager.forms import WorkerListFilter, NameExactFilterForm, ProjectCreateForm, ProjectUpdateForm
from task_manager.mixins import QuerysetFilterByUserMixin, TaskPermissionRequiredMixin
from task_manager.models import Worker, Task, Project, Team, Activity, Comment
from task_manager.views import (
    ListFilterView,
    IndexView,
    TaskListFilterView,
    TaskDetailView,
    TaskUpdateView,
    TaskDeleteView,
    ProjectListFilterView,
    ProjectDetailView,
    ProjectUpdateView,
    ProjectDeleteView,
    TeamListFilterView,
)


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


class TaskDetailViewTest(TestCase):
    view_name = "task_manager:task_detail"
    pk_url_kwargs = TaskDetailView.pk_url_kwarg

    def setUp(self) -> None:
        self.user_project = Project.objects.create(
            name="Test project name"
        )
        user_team = Team.objects.create(
            name="Test user team name "
        )
        user_team.projects.add(self.user_project)
        self.user = get_user_model().objects.create_user(
            username="test_admin",
            password="123456",
            team=user_team
        )
        self.task_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=self.user_project
        )

        self.client.force_login(self.user)

    def test_task_detail_login_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_task_detail_permission_required_if_task_not_in_user_project(self) -> None:
        user = self.user
        project = Project.objects.create(
            name="Test project name"
        )
        task_not_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=project
        )
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task_not_in_user_project.pk}
        )

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_perm("task_manager.view_task"))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        permission = Permission.objects.get(codename="view_task")
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_should_use_has_permission_from_task_permission_required_mixin(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )

        with patch(f"{TaskPermissionRequiredMixin.__module__}."
                   "TaskPermissionRequiredMixin.has_permission") as mock_method:
            mock_method.return_value = True
            self.client.get(url)

            mock_method.assert_called()

    def test_context_should_contain_comment_form(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )

        response = self.client.get(url)

        self.assertIsInstance(
            response.context["comment_form"],
            TaskDetailView.comment_form
        )

    def test_post_should_create_task_comment(self) -> None:
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )

        data = {"content": "Comment text"}

        self.assertQuerySetEqual(
            task.comments.all(),
            Comment.objects.none()
        )

        self.client.post(url, data=data)

        self.assertEqual(
            task.comments.all().count(),
            1
        )

    def test_post_should_log_activity_if_comment_created(self) -> None:
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )

        data = {"content": "Comment text"}

        self.assertQuerySetEqual(
            task.comments.all(),
            Comment.objects.none()
        )
        self.assertQuerySetEqual(
            task.activities.all(),
            Activity.objects.none()
        )

        self.client.post(url, data=data)

        self.assertEqual(
            task.comments.all().count(),
            1
        )

        self.assertEqual(
            task.activities.filter(type=Activity.ActivityTypeChoices.ADD_COMMENT).count(),
            1
        )

    def test_post_should_toggle_assignee(self) -> None:
        user = self.user
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )

        self.assertNotIn(
            user,
            task.assignees.all()
        )

        data = {"assign_to_me": ""}
        self.client.post(url, data=data)

        self.assertIn(
            user,
            task.assignees.all()
        )

        self.client.post(url, data=data)
        self.assertNotIn(
            user,
            task.assignees.all()
        )

    def test_post_should_log_activity_if_assignee_toggled(self) -> None:
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )

        self.assertQuerySetEqual(
            task.activities.all(),
            Activity.objects.none()
        )

        data = {"assign_to_me": ""}
        self.client.post(url, data=data)

        self.assertEqual(
            task.activities.filter(type=Activity.ActivityTypeChoices.UPDATE_TASK).count(),
            1
        )

    def test_post_should_redirect_to_task_detail_page(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )

        data = {"comment": "Some text"}

        response = self.client.post(url, data=data)

        self.assertEqual(
            response.status_code,
            302
        )
        self.assertEqual(
            response.url,
            url
        )


class TaskUpdateViewTest(TestCase):
    view_name = "task_manager:task_update"
    pk_url_kwargs = TaskUpdateView.pk_url_kwarg

    def setUp(self) -> None:
        self.user_project = Project.objects.create(
            name="Test project name"
        )
        user_team = Team.objects.create(
            name="Test user team name "
        )
        user_team.projects.add(self.user_project)
        self.user = get_user_model().objects.create_user(
            username="test_admin",
            password="123456",
            team=user_team
        )
        self.task_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=self.user_project
        )

        self.client.force_login(self.user)

    def test_task_detail_login_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_task_detail_permission_required_if_task_not_in_user_project(self) -> None:
        user = self.user
        project = Project.objects.create(
            name="Test project name"
        )
        task_not_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=project
        )
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task_not_in_user_project.pk}
        )

        self.assertFalse(user.is_superuser)
        permission_required = ("task_manager.view_task", "task_manager.change_task")
        self.assertFalse(user.has_perms(permission_required))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        view_permission = Permission.objects.get(codename="view_task")
        change_permission = Permission.objects.get(codename="change_task")
        user.user_permissions.add(view_permission, change_permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_should_use_has_permission_from_task_permission_required_mixin(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )

        with patch(f"{TaskPermissionRequiredMixin.__module__}."
                   "TaskPermissionRequiredMixin.has_permission") as mock_method:
            mock_method.return_value = True
            self.client.get(url)

            mock_method.assert_called()

    def test_should_log_activity_if_task_updated(self) -> None:
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )
        data = {
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "is_completed": False
        }

        self.assertQuerySetEqual(
            task.activities.all(),
            Activity.objects.none()
        )

        self.client.post(url, data=data)

        self.assertEqual(
            task.activities.filter(type=Activity.ActivityTypeChoices.UPDATE_TASK).count(),
            1
        )

    def test_if_task_updated_should_redirect_to_task_detail_page(self) -> None:
        task = self.task_in_user_project
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task.pk}
        )

        data = {
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "is_completed": False

        }

        self.assertQuerySetEqual(
            task.activities.all(),
            Activity.objects.none()
        )

        response = self.client.post(url, data=data)

        self.assertEqual(
            response.status_code,
            302
        )
        self.assertEqual(
            response.url,
            reverse("task_manager:task_detail", kwargs={self.pk_url_kwargs: task.pk})
        )


class TaskDeleteViewTest(TestCase):
    view_name = "task_manager:task_delete"
    pk_url_kwargs = TaskDeleteView.pk_url_kwarg

    def setUp(self) -> None:
        self.user_project = Project.objects.create(
            name="Test project name"
        )
        user_team = Team.objects.create(
            name="Test user team name "
        )
        user_team.projects.add(self.user_project)
        self.user = get_user_model().objects.create_user(
            username="test_admin",
            password="123456",
            team=user_team
        )
        self.task_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=self.user_project
        )

        self.client.force_login(self.user)

    def test_task_detail_login_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_task_detail_permission_required_if_task_not_in_user_project(self) -> None:
        user = self.user
        project = Project.objects.create(
            name="Test project name"
        )
        task_not_in_user_project = Task.objects.create(
            name="Test task name",
            description="Test descriptions",
            project=project
        )
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: task_not_in_user_project.pk}
        )

        self.assertFalse(user.is_superuser)
        permission_required = ("task_manager.view_task", "task_manager.delete_task")
        self.assertFalse(user.has_perms(permission_required))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        view_permission = Permission.objects.get(codename="view_task")
        change_permission = Permission.objects.get(codename="delete_task")
        user.user_permissions.add(view_permission, change_permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_should_use_has_permission_from_task_permission_required_mixin(self) -> None:
        url = reverse(
            self.view_name, kwargs={self.pk_url_kwargs: self.task_in_user_project.pk}
        )

        with patch(f"{TaskPermissionRequiredMixin.__module__}."
                   "TaskPermissionRequiredMixin.has_permission") as mock_method:
            mock_method.return_value = True
            self.client.get(url)

            mock_method.assert_called()


class ProjectListFilterViewTest(TestCase):
    url = reverse("task_manager:project_list")
    fake = Faker()

    def setUp(self) -> None:
        self.user_project = Project.objects.create(
            name="Test project name"
        )
        team = Team.objects.create(
            name="Test team name"
        )
        team.projects.add(self.user_project)
        self.user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456",
            team=team
        )

        self.client.force_login(self.user)

    def test_project_list_filter_login_required(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_project_list_filter_paginated_by_value(self) -> None:
        self.assertEqual(
            ProjectListFilterView.paginate_by,
            settings.DEFAULT_PAGINATE_BY
        )

    def test_project_list_filter_paginated(self) -> None:
        paginated_by = ProjectListFilterView.paginate_by
        num_user_projects = Project.objects.filter_by_user(self.user).count()

        if paginated_by >= num_user_projects:
            num_additional_projects = paginated_by - num_user_projects + 1
            for _ in range(num_additional_projects):
                pr = Project.objects.create(
                    name=self.fake.sentence(nb_words=2)
                )
                pr.teams.add(self.user.team)

        response = self.client.get(self.url)
        expected_qs = Project.objects.filter_by_user(self.user)[:paginated_by]
        self.assertQuerySetEqual(
            response.context["project_list"],
            expected_qs,
            ordered=False
        )

    def test_project_list_filter_use_correct_filter_form(self) -> None:
        response = self.client.get(self.url)

        self.assertIsInstance(
            response.context[ProjectListFilterView.filter_context_name],
            NameExactFilterForm
        )

    def test_project_list_filter_filtered(self) -> None:

        for _ in range(5):
            pr = Project.objects.create(
                name=self.fake.sentence(nb_words=2)
            )
            pr.teams.add(self.user.team)

        response = self.client.get(
            self.url, data={"name": self.user_project.name}
        )

        expected_qs = Project.objects.filter_by_user(
            self.user
        ).filter(name=self.user_project.name)

        self.assertQuerySetEqual(
            response.context["project_list"],
            expected_qs,
            ordered=False
        )

    def test_projects_list_should_contain_only_available_for_user_projects(self) -> None:
        for _ in range(5):
            Project.objects.create(
                name=self.fake.sentence(nb_words=2)
            )
        response = self.client.get(self.url)

        expected_qs = Project.objects.filter_by_user(self.user)

        self.assertQuerySetEqual(
            response.context["project_list"],
            expected_qs,
            ordered=False
        )

    def test_should_used_qet_queryset_method_from_queryset_filter_by_user_mixin(self) -> None:
        with patch(f"{QuerysetFilterByUserMixin.__module__}."
                   "QuerysetFilterByUserMixin.get_queryset") as mock_method:
            mock_method.return_value = Project.objects.filter_by_user(self.user)
            self.client.get(self.url)

            mock_method.assert_called()


class ProjectDetailViewTest(TestCase):
    view_name = "task_manager:project_detail"

    def setUp(self) -> None:
        self.project = Project.objects.create(
            name="Test project name"
        )
        team = Team.objects.create(
            name="Test team name"
        )

        self.user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456",
            team=team
        )

        self.client.force_login(self.user)

    def test_project_detail_login_required(self) -> None:
        self.user.team.projects.add(self.project)

        url = reverse(
            self.view_name, kwargs={ProjectDetailView.pk_url_kwarg: self.project.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_project_detail_permissions_required_if_user_not_in_project(self) -> None:
        user = self.user
        url = reverse(
            self.view_name, kwargs={ProjectDetailView.pk_url_kwarg: self.project.id}
        )

        self.assertNotIn(
            self.project, user.team.projects.all()
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_project_detail_available_if_user_have_permission(self) -> None:
        user = self.user
        url = reverse(
            self.view_name, kwargs={ProjectDetailView.pk_url_kwarg: self.project.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        perm = Permission.objects.get(codename="view_project")
        user.user_permissions.add(perm)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_project_detail_available_if_superuser(self) -> None:
        user = self.user
        url = reverse(
            self.view_name, kwargs={ProjectDetailView.pk_url_kwarg: self.project.id}
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        user.is_superuser = True
        user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_project_detail_available_if_user_in_project(self) -> None:
        user = self.user
        url = reverse(
            self.view_name, kwargs={ProjectDetailView.pk_url_kwarg: self.project.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        user.team.projects.add(self.project)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ProjectCreateViewTest(TestCase):
    url = reverse("task_manager:project_create")

    def setUp(self) -> None:
        user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456"
        )
        view_perm = Permission.objects.get(codename="view_project")
        add_perm = Permission.objects.get(codename="add_project")
        user.user_permissions.add(view_perm, add_perm)
        self.user = user
        self.client.force_login(user)

    def test_project_create_login_required(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_project_create_permissions_required(self) -> None:
        user = self.user
        permission_required = ("task_manager.view_project", "task_manager.add_project")
        self.assertTrue(user.has_perms(permission_required))

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        user.user_permissions.clear()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_project_create_should_use_correct_form(self) -> None:
        response = self.client.get(self.url)

        self.assertIsInstance(
            response.context["form"],
            ProjectCreateForm
        )

    def test_project_create_should_redirect_to_project_detail_if_created(self) -> None:
        project_name = "Test project name"
        self.assertFalse(
            Project.objects.filter(name=project_name).exists()
        )
        data = {
            "name": project_name,
            "description": "Test description"
        }
        response = self.client.post(self.url, data=data)

        created_project = Project.objects.get(name=project_name)
        expected_url = reverse(
            "task_manager:project_detail",
            kwargs={ProjectDetailView.pk_url_kwarg: created_project.pk}
        )
        self.assertEqual(response.url, expected_url)


class ProjectUpdateViewTest(TestCase):
    view_name = "task_manager:project_update"

    def setUp(self) -> None:
        self.project = Project.objects.create(
            name="Test project name",
            description="Test descriptions"
        )
        user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456"
        )
        view_perm = Permission.objects.get(codename="view_project")
        add_perm = Permission.objects.get(codename="change_project")
        user.user_permissions.add(view_perm, add_perm)
        self.user = user
        self.client.force_login(user)

    def test_project_update_login_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={ProjectUpdateView.pk_url_kwarg: self.project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_project_update_permissions_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={ProjectUpdateView.pk_url_kwarg: self.project.pk}
        )
        user = self.user
        permission_required = ("task_manager.view_project", "task_manager.change_project")
        self.assertTrue(user.has_perms(permission_required))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        user.user_permissions.clear()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_project_update_should_use_correct_form(self) -> None:
        url = reverse(
            self.view_name, kwargs={ProjectUpdateView.pk_url_kwarg: self.project.pk}
        )
        response = self.client.get(url)

        self.assertIsInstance(
            response.context["form"],
            ProjectUpdateForm
        )

    def test_project_update_should_redirect_to_project_detail_if_updated(self) -> None:
        project = self.project
        url = reverse(
            self.view_name, kwargs={ProjectUpdateView.pk_url_kwarg: project.pk}
        )
        project_name = "New test project name"

        data = {
            "name": project_name,
            "description": "New test description"
        }
        response = self.client.post(url, data=data)

        project.refresh_from_db()
        self.assertEqual(
            self.project.name,
            project_name
        )

        expected_url = reverse(
            "task_manager:project_detail",
            kwargs={ProjectDetailView.pk_url_kwarg: project.pk}
        )
        self.assertEqual(response.url, expected_url)


class ProjectDeleteViewTest(TestCase):
    view_name = "task_manager:project_delete"

    def setUp(self) -> None:
        self.project = Project.objects.create(
            name="Test project name",
            description="Test descriptions"
        )
        user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456"
        )
        view_perm = Permission.objects.get(codename="view_project")
        add_perm = Permission.objects.get(codename="delete_project")
        user.user_permissions.add(view_perm, add_perm)
        self.user = user
        self.client.force_login(user)

    def test_project_delete_login_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={ProjectDeleteView.pk_url_kwarg: self.project.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_project_delete_permissions_required(self) -> None:
        url = reverse(
            self.view_name, kwargs={ProjectDeleteView.pk_url_kwarg: self.project.pk}
        )
        user = self.user
        permission_required = ("task_manager.view_project", "task_manager.delete_project")
        self.assertTrue(user.has_perms(permission_required))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        user.user_permissions.clear()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_project_deleted_should_redirect_to_project_list_if_deleted(self) -> None:
        project = self.project
        url = reverse(
            self.view_name, kwargs={ProjectDeleteView.pk_url_kwarg: project.pk}
        )

        response = self.client.post(url)

        self.assertFalse(
            Project.objects.filter(pk=project.pk).exists()
        )

        expected_url = reverse("task_manager:project_list")
        self.assertEqual(response.url, expected_url)


class TeamListFilterViewTest(TestCase):
    url = reverse("task_manager:team_list")
    fake = Faker()

    def setUp(self) -> None:
        for _ in range(5):
            Team.objects.create(
                name=self.fake.sentence(nb_words=2)
            )

        self.team = Team.objects.create(
            name="Test team name"
        )
        self.user = get_user_model().objects.create_user(
            username="test_user_name",
            password="123456",
            team=self.team
        )

        self.user_with_default_team = get_user_model().objects.create_user(
            username="test_user_default_team",
            password="123456",
            team=Team.get_default_team()
        )

        self.user_with_perm = get_user_model().objects.create_user(
            username="test_user_with_permission",
            password="123456",
        )
        view_perm = Permission.objects.get(codename="view_team")
        self.user_with_perm.user_permissions.add(view_perm)

        self.superuser = get_user_model().objects.create_superuser(
            username="test_superuser",
            password="123456",
        )

    def test_team_list_filter_login_required(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_team_list_filter_paginated_by_value(self) -> None:
        self.assertEqual(
            TeamListFilterView.paginate_by,
            settings.DEFAULT_PAGINATE_BY
        )

    def test_team_list_filter_paginated(self) -> None:
        superuser = self.superuser
        paginated_by = TeamListFilterView.paginate_by
        team_qs = Team.objects.exclude_default_team()
        num_teams = team_qs.filter_by_user(superuser).count()

        if paginated_by >= num_teams:
            num_additional_teams = paginated_by - num_teams + 1
            for _ in range(num_additional_teams):
                Team.objects.create(
                    name=self.fake.sentence(nb_words=2)
                )

        team_qs = Team.objects.exclude_default_team()
        expected_qs = team_qs.filter_by_user(superuser)[:TeamListFilterView.paginate_by]

        self.client.force_login(superuser)
        response = self.client.get(self.url)
        self.assertQuerySetEqual(
            response.context["team_list"],
            expected_qs,
            ordered=False
        )

    def test_team_list_filter_use_correct_filter_form(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertIsInstance(
            response.context[TeamListFilterView.filter_context_name],
            NameExactFilterForm
        )

    def test_team_list_filter_filtered(self) -> None:
        self.client.force_login(self.superuser)
        team_qs = Team.objects.exclude_default_team().filter_by_user(self.superuser)
        expected_qs = team_qs.filter(name=self.team.name)

        response = self.client.get(self.url, data={"name": self.team.name})
        self.assertQuerySetEqual(
            response.context["team_list"],
            expected_qs,
            ordered=False
        )

    def test_team_list_should_not_contain_default_team(self) -> None:
        user_list = [
            self.user,
            self.user_with_default_team,
            self.user_with_perm,
            self.superuser
        ]
        default_team = Team.get_default_team()
        for user in user_list:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(self.url)

                self.assertNotIn(default_team, response.context["team_list"])

    def test_team_list_queryset_value_if_user_with_team(self) -> None:
        user = self.user

        expected_qs = Team.objects.exclude_default_team().filter_by_user(user)

        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertQuerySetEqual(
            response.context["team_list"], expected_qs, ordered=False
        )

    def test_team_list_queryset_value_if_user_with_default_team(self) -> None:
        user = self.user_with_default_team

        expected_qs = Team.objects.none()

        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertQuerySetEqual(
            response.context["team_list"], expected_qs, ordered=False
        )

    def test_team_list_queryset_value_if_user_has_permission(self) -> None:
        user = self.user_with_perm

        expected_qs = Team.objects.exclude_default_team()[:TeamListFilterView.paginate_by]

        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertQuerySetEqual(
            response.context["team_list"], expected_qs, ordered=False
        )

    def test_team_list_queryset_value_if_user_is_superuser(self) -> None:
        user = self.superuser
        expected_qs = Team.objects.exclude_default_team()[:TeamListFilterView.paginate_by]

        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertQuerySetEqual(
            response.context["team_list"], expected_qs, ordered=False
        )
