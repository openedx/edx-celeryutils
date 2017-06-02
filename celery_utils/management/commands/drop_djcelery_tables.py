"""
This command will drop the tables included in django-celery's
migrations, which are included when we bump that to 3.2.1

If the tables are not empty, this command will show a message and exit.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
import logging
from textwrap import dedent

from djcelery.models import (CrontabSchedule, IntervalSchedule, PeriodicTask,  # pylint:disable=import-error
                             PeriodicTasks, TaskMeta, TaskSetMeta, TaskState, WorkerState)

from django.core.management.base import BaseCommand
from django.db import connection

log = logging.getLogger(__name__)

DJCELERY_MODEL_TABLES = OrderedDict({
    PeriodicTask: '\"djcelery_periodictask\"',  # must be before crontab, interval
    TaskState: '\"djcelery_taskstate\"',  # must be before workerstate
})
DJCELERY_MODEL_TABLES.update({
    CrontabSchedule: '\"djcelery_crontabschedule\"',
    IntervalSchedule: '\"djcelery_intervalschedule\"',
    PeriodicTasks: '\"djcelery_periodictasks\"',
    WorkerState: '\"djcelery_workerstate\"',
    TaskSetMeta: '\"celery_tasksetmeta\"',
    TaskMeta: '\"celery_taskmeta\"',
})


class Command(BaseCommand):
    """
    Drop the database tables used by django-celery, iff they are empty.
    """
    help = dedent(__doc__).strip()

    def _log_execute(self, cursor, sql, context=""):
        """
        Log a given SQL input (as string) before executing it.
        """
        log.info("{} raw SQL:\n{}".format(context, sql))
        cursor.execute(sql)

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                log.info("Acquiring tables locks on {}".format(", ".join(DJCELERY_MODEL_TABLES.values())))
                lock_sql = "LOCK TABLES {}".format(
                    ", ".join(
                        "{} WRITE".format(table)
                        for table in DJCELERY_MODEL_TABLES.values()
                    )
                )
                self._log_execute(cursor, lock_sql, 'table lock')

                for model in DJCELERY_MODEL_TABLES.keys():
                    assert model.objects.all().count() == 0
                log.info("Tables are confirmed empty and I hold a lock on all of them, proceeding to DROP TABLE")

                for table_name in DJCELERY_MODEL_TABLES.values():
                    drop_sql = "DROP TABLE IF EXISTS {} CASCADE".format(table_name)
                    self._log_execute(cursor, drop_sql, "drop {}".format(table_name))
                log.info("Tables have been dropped, proceed with djcelery migrations as needed.")
            except AssertionError:
                output = (
                    "The tables associated with django-celery are in use and non-empty.\n"
                    "This presents a problem for edx-celeryutils, as we need to upgrade"
                    "the installed version of django-celery, and the newer version uses"
                    "migrations where the previous version used sync_db.\nYou, dear user,"
                    "have won the special prize of being a corner case we at edx.org were"
                    "not aware of.\nPlease try to rectify the djcelery tables on your own,"
                    "using --skip-initial or other methods as needed. If you do not, the"
                    "next release of edx-celeryutils will try perform django-celery's"
                    "initial migration and fail with a 'table already exists' error."
                )
                log.info(output)
