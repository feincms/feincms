# coding: utf-8
from django.core.management import CommandError
from django.core.management.color import no_style
from django.core.management.sql import sql_delete, sql_all
from django.db import connections, transaction, DEFAULT_DB_ALIAS
import feincms.models

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


def reset_page_db():
    using = DEFAULT_DB_ALIAS
    connection = connections[using]
    sql_list = sql_delete(feincms.module.page.models, no_style(), connection)
    sql_list += sql_all(feincms.module.page.models, no_style(), connection)
    try:
        cursor = connection.cursor()
        for sql in sql_list:
            cursor.execute(sql)
    except Exception, e:
        transaction.rollback_unless_managed()
        raise CommandError("Error: database couldn't be reset: %s" % e)
    else:
        transaction.commit_unless_managed()
