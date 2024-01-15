from django.db.models import Q
from django.test import SimpleTestCase, TestCase

from task_manager.models import NameInfo, Position, Tag, TaskType, Team
from task_manager.querysets import TeamQuerySet


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
