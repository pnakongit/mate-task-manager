from django.test import SimpleTestCase

from task_manager.models import NameInfo


class NameInfoTest(SimpleTestCase):

    def test_name_info_should_be_abstract_class(self) -> None:
        self.assertTrue(NameInfo._meta.abstract)
