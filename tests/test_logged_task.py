"""
Testing persistent tasks.

A task built with the LoggedTask base class is imported from test_utils.tasks.
    * simple_logged_task -
        Emits an "INFO" level log statement as soon as the task returns.
        Note that this will occur after the task runs if the task is run under
        always_eager, but it will not be emitted if task.apply() is called directly.

"""

from __future__ import absolute_import, division, print_function, unicode_literals

from billiard.einfo import ExceptionInfo
import mock

from celery_utils.logged_task import LoggedTask
from test_utils import tasks


def test_logged_task_without_failure():
    with mock.patch('celery_utils.logged_task.log') as mocklog:
        result = tasks.simple_logged_task.apply_async(args=(3, 4), kwargs={'c': 5}, task_id='papers-please')
        result.wait()

    stringc = 'c'  # Handle different string repr for python 2 and 3
    logmessage = "Task test_utils.tasks.simple_logged_task[papers-please] submitted with arguments (3, 4), {%r: 5}"
    mocklog.info.assert_called_with(logmessage % stringc)


def test_on_retry_formatting():
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


def test_no_capture_on_retry_unless_exception():
    task = LoggedTask()
    task_id = 'my-id'
    args = (1, 2)
    kwargs = {'c': 3}
    exc = None
    einfo = None
    with mock.patch('celery_utils.logged_task.log') as mocklog:
        task.on_retry(exc, task_id, args, kwargs, einfo)
        assert not mocklog.warning.called


def test_on_failure_formatting():
    with mock.patch('celery_utils.logged_task.log') as mocklog:
        result = tasks.failing_logged_task.apply_async()
        try:
            result.wait()
        except ValueError:
            pass
        logmessage = mocklog.warning.call_args[0][0]
        assert 'ValueError' in logmessage
