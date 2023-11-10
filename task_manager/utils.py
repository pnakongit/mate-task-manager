import datetime


def get_next_three_days_date() -> datetime.date:
    return datetime.date.today() + datetime.timedelta(days=3)
