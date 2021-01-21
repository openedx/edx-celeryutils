"""
Testing persistent tasks.

A task built with the LoggedTask base class is imported from test_utils.tasks.
    * simple_logged_task -
        Emits an "INFO" level log statement as soon as the task returns.
        Note that this will occur after the task runs if the task is run under
        always_eager, but it will not be emitted if task.apply() is called directly.

"""

from unittest import mock

from billiard.einfo import ExceptionInfo
import pytest

from celery_utils.logged_task import LoggedTask
from test_utils import tasks


def test_no_failure():
    with mock.patch('celery_utils.logged_task.log') as mocklog:
        result = tasks.simple_logged_task.apply_async(args=(3, 4), kwargs={'c': 5}, task_id='papers-please')
        result.wait()

    stringc = 'c'  # Handle different string repr for python 2 and 3
    logmessage = "Task test_utils.tasks.simple_logged_task[papers-please] submitted with arguments (3, 4), {%r: 5}"
    mocklog.info.assert_called_with(logmessage % stringc)
    assert not mocklog.error.called


def test_failure():
    with mock.patch('celery_utils.logged_task.log') as mocklog:
        result = tasks.failed_logged_task.delay()
        with pytest.raises(ValueError):
            result.wait(retry=False)
    assert result.status == 'FAILURE'
    assert mocklog.error.called
    log_message = mocklog.error.call_args[0][0]
    assert '[{}] failed due to Traceback'.format(result.task_id) in log_message


def test_retry():
    # With celery running in eager mode, the on_retry handler doesn't actually
    # get called when a retry happens.  Here we just try to show that when it does
    # get called, the log message is formatted correctly.
    task = LoggedTask()
    task_id = 'my-id'
    args = (1, 2)
    kwargs = {'c': 3}
    try:
        raise ValueError()
    except ValueError as exc:
        einfo = ExceptionInfo()
        with mock.patch('celery_utils.logged_task.log') as mocklog:
            task.on_retry(exc, task_id, args, kwargs, einfo)
            logmessage = mocklog.warning.call_args[0][0]
            assert '[{}]'.format(task_id) in logmessage
            assert einfo.traceback in logmessage
