import datetime

from django.test import TestCase

from task_manager.utils import get_next_three_days_date


class GetNextThreeDaysDateTest(TestCase):

    def test_should_return_plus_tree_day_from_today(self) -> None:
        expected_date = datetime.date.today() + datetime.timedelta(days=3)

        self.assertEqual(get_next_three_days_date(), expected_date)
