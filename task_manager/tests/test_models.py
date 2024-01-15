from django.test import SimpleTestCase, TestCase

from task_manager.models import NameInfo, Position


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
