# coding: utf-8

import datetime


def mock_datetime():
    class MockDatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return datetime.datetime(2012, 6, 1)
    return MockDatetime


def mock_date():
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return datetime.date(2012, 6, 1)
    return MockDate
