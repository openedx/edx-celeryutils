"""
Test management command to cleanup resolved tasks.
"""

from datetime import timedelta

import pytest

from django.core.management import call_command
from django.utils.timezone import now

from .... import models

DAY = timedelta(days=1)
MONTH_AGO = now() - (30 * DAY)


@pytest.fixture
def failed_tasks():
    """
    Create a diverse set of FailedTask records:
        * Three representing runs of a task named 'task'
          * One resolved more than a month ago (31 days)
          * One resolved less than a month ago (29 days)
          * One unresolved task
        * One representing a run of a task named 'other'
          * Resolved more than a month ago (31 days)
    """
    return [
        models.FailedTask.objects.create(
            task_name='task',
            datetime_resolved=MONTH_AGO - DAY,
            task_id='old',
        ),
        models.FailedTask.objects.create(
            task_name='task',
            datetime_resolved=MONTH_AGO + DAY,
            task_id='new',
        ),
        models.FailedTask.objects.create(
            task_name='task',
            datetime_resolved=None,
            task_id='unresolved',
        ),
        models.FailedTask.objects.create(
            task_name='other',
            datetime_resolved=MONTH_AGO - DAY,
            task_id='other',
        ),
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('args', 'remaining_task_ids'),
    [
        ([], {'new', 'unresolved'}),
        (['--task-name=task'], {'new', 'unresolved', 'other'}),
        (['--age=0'], {'unresolved'}),
        (['--age=0', '--task-name=task'], {'unresolved', 'other'}),
        (['--dry-run'], {'old', 'new', 'unresolved', 'other'}),
    ],
)
@pytest.mark.usefixtures('failed_tasks')
def test_call_command(args, remaining_task_ids):
    call_command('cleanup_resolved_tasks', *args)
    results = set(models.FailedTask.objects.values_list('task_id', flat=True))
    assert remaining_task_ids == results
