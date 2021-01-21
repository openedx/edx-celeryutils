"""
Test management command to reapply failed tasks.
"""

from collections import Counter
from datetime import datetime
from unittest import mock

import pytest

from django.core.management import call_command

from test_utils import tasks

from .... import models


@pytest.fixture
def failed_tasks():
    """
    Create a set of FailedTask records.

    * Two representing fallible_task runs:
        * One that will fail again
        * One that will succeed when run again
    * One respresenting a passing_task run, that will always pass.
    """
    return [
        models.FailedTask.objects.create(
            task_name=tasks.fallible_task.name,
            task_id='fail_again',
            args=[],
            kwargs={"error_message": "Err, yo!"},
            exc='UhOhError().',
        ),
        models.FailedTask.objects.create(
            task_name=tasks.fallible_task.name,
            task_id='will_succeed',
            args=[],
            kwargs={},
            exc='NetworkErrorMaybe?()',
        ),
        models.FailedTask.objects.create(
            task_name=tasks.passing_task.name,
            task_id='other_task',
            args=[],
            kwargs={},
            exc='RaceCondition()',
        ),
    ]


@pytest.mark.django_db
@pytest.mark.usefixtures('failed_tasks')
def test_call_command():
    call_command('reapply_tasks')
    assert_unresolved(models.FailedTask.objects.get(task_id='fail_again'))
    assert_resolved(models.FailedTask.objects.get(task_id='will_succeed'))
    assert_resolved(models.FailedTask.objects.get(task_id='other_task'))


@pytest.mark.django_db
@pytest.mark.usefixtures('failed_tasks')
def test_call_command_with_specified_task():
    call_command('reapply_tasks', f'--task-name={tasks.fallible_task.name}')
    assert_unresolved(models.FailedTask.objects.get(task_id='fail_again'))
    assert_resolved(models.FailedTask.objects.get(task_id='will_succeed'))
    assert_unresolved(models.FailedTask.objects.get(task_id='other_task'))


@pytest.mark.django_db
@pytest.mark.usefixtures('failed_tasks')
def test_duplicate_tasks():
    models.FailedTask.objects.create(
        task_name=tasks.fallible_task.name,
        task_id='will_succeed',
        args=[],
        kwargs={},
        exc='AlsoThisOtherError()',
    )
    # Verify that only one task got run for this task_id.
    # pylint: disable=no-member
    with mock.patch.object(tasks.fallible_task, 'apply_async', wraps=tasks.fallible_task.apply_async) as mock_apply:
        call_command('reapply_tasks')
        task_id_counts = Counter(call[2]['task_id'] for call in mock_apply.mock_calls)
        assert task_id_counts['will_succeed'] == 1
    # Verify that both tasks matching that task_id are resolved.
    will_succeed_tasks = models.FailedTask.objects.filter(task_id='will_succeed').all()
    assert len(will_succeed_tasks) == 2
    for task_object in will_succeed_tasks:
        assert_resolved(task_object)


def assert_resolved(task_object):
    """
    Raises an assertion error if the task failed to complete successfully
    and record its resolution in the failedtask record.
    """
    assert isinstance(task_object.datetime_resolved, datetime)


def assert_unresolved(task_object):
    """
    Raises an assertion error if the task completed successfully.
    The resolved_datetime will still be None.
    """
    assert task_object.datetime_resolved is None
