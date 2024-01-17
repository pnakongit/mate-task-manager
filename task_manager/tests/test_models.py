import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from task_manager.managers import WorkerManager
from task_manager.models import NameInfo, Position, Tag, TaskType, Team, Worker, Project, Task
from task_manager.querysets import TeamQuerySet, ProjectQuerySet, TaskQuerySet


class NameInfoTest(SimpleTestCase):

    def test_name_info_should_be_abstract_class(self) -> None:
        self.assertTrue(NameInfo._meta.abstract)


class PositionTest(TestCase):

    def test_should_inherits_from_name_info(self) -> None:
        self.assertTrue(issubclass(Position, NameInfo))

    def test_test_string_representation(self) -> None:
        self.assertIs(Position.__str__,
                      NameInfo.__str__,
                      msg="Position model should use the __str__ method from NameInfo model")
        position = Position.objects.create(name="Test_name")
        self.assertEqual(str(position), position.name)


class TagTest(SimpleTestCase):

    def test_should_inherits_from_name_info(self) -> None:
        self.assertTrue(issubclass(Tag, NameInfo))


class TaskTypeTest(SimpleTestCase):
    def test_should_inherits_from_name_info(self) -> None:
        self.assertTrue(issubclass(TaskType, NameInfo))


class TeamTest(TestCase):
    default_team_name = "No team"

    def test_should_inherits_from_name_info(self) -> None:
        self.assertTrue(issubclass(Team, NameInfo))

    def test_should_use_teamqueryset(self) -> None:
        queryset = Team.objects.get_queryset()
        self.assertIsInstance(queryset, TeamQuerySet)

    def test_get_default_team_should_created_team_with_specific_name(self) -> None:
        self.assertFalse(
            Team.objects.filter(name=self.default_team_name).exists()
        )

        team = Team.get_default_team()

        self.assertEqual(team.name, self.default_team_name)

    def test_get_default_team_should_create_default_team(self) -> None:
        self.assertFalse(
            Team.objects.filter(name=self.default_team_name).exists()
        )
        Team.get_default_team()
        self.assertTrue(
            Team.objects.filter(name=self.default_team_name).exists()
        )

    def test_get_default_team_should_return_team_if_default_team_exist(self) -> None:
        obj = Team.get_default_team()
        self.assertEqual(obj, Team.get_default_team())

    def test_get_exclude_team_should_exclude_default_team(self) -> None:
        expected_q_obj = ~Q(pk=Team.get_default_team().pk)
        self.assertEqual(Team.get_exclude_team(), expected_q_obj)


class WorkerTest(TestCase):

    def setUp(self) -> None:
        self.worker = Worker.objects.create_user(
            username="test_username",
            email="test_mail",
            password="1234567",
            first_name="Ivan",
            last_name="Mazepa"
        )

    def test_model_use_workermanager(self) -> None:
        self.assertIsInstance(
            Worker.objects,
            WorkerManager
        )

    def test_string_representation(self) -> None:
        expected_str = f"{self.worker.first_name} {self.worker.last_name}"
        self.assertEqual(str(self.worker), expected_str)

    def test_team_field_default_value_is_none(self) -> None:
        self.assertIsNone(
            Worker._meta.get_field("team").get_default()
        )

    def test_save_method_set_default_team_if_team_none(self) -> None:
        self.worker.team = None
        self.worker.save()

        self.assertEqual(self.worker.team, Team.get_default_team())

    def test_save_method_set_team_value_if_team_not_none(self) -> None:
        team = Team.objects.create(name="Test team")
        self.worker.team = team
        self.worker.save()

        self.assertEqual(self.worker.team, team)


class ProjectTest(TestCase):

    def test_should_use_projectqueryset(self) -> None:
        queryset = Project.objects.get_queryset()
        self.assertIsInstance(queryset, ProjectQuerySet)

    def test_string_representation(self) -> None:
        project = Project.objects.create(
            name="Test project"
        )
        self.assertEqual(str(project), project.name)


class TaskTest(TestCase):

    def setUp(self) -> None:
        project = Project.objects.create(
            name="Test project name",
            description="Test description"
        )

        worker = Worker.objects.create_user(
            username="test_username",
            email="test_mail",
            password="1234567",
            first_name="Ivan",
            last_name="Mazepa"
        )

        task_type = TaskType.objects.create(
            name="Test task_type"
        )

        self.task = Task(
            name="Test task name",
            description="Test description",
            project=project,
            creator=worker,
            task_type=task_type
        )

    def test_model_use_taskqueryset(self) -> None:
        self.assertIsInstance(
            Task.objects.get_queryset(),
            TaskQuerySet
        )

    def test_string_representation(self) -> None:
        expected_str = f"{self.task.pk} {self.task.name}"
        self.assertEqual(str(self.task), expected_str)

    def test_deadline_field_validator_valid_value(self) -> None:
        valid_date = datetime.date.today()

        task = self.task
        task.deadline = valid_date
        task.full_clean()
        task.save()

        self.assertEqual(task.deadline, valid_date)

    def test_deadline_field_validator_invalid_value(self) -> None:
        invalid_date = datetime.date.today() - datetime.timedelta(days=1)

        task = self.task
        with self.assertRaises(ValidationError):
            task.deadline = invalid_date
            task.full_clean()
            task.save()

    def test_deadline_field_validator_error_message(self) -> None:
        task = self.task
        today_date = datetime.date.today()
        invalid_date = today_date - datetime.timedelta(days=1)
        expected_message = f"Ensure date is greater than or equal to {today_date}."

        with self.assertRaisesMessage(ValidationError, expected_message):
            task.deadline = invalid_date
            task.full_clean()
            task.save()

    def test_model_has_necessary_indexes(self) -> None:
        necessary_indexes = [
            {"fields": ["name"], "name": "name_idx"},
            {"fields": ["description"], "name": "description_idx"}
        ]

        indexes = [
            {"fields": idx.fields, "name": idx.name}
            for idx in Task._meta.indexes
        ]

        self.assertEqual(indexes, necessary_indexes)
