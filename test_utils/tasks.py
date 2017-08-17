"""
Tasks used in tests
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from celery_utils import logged_task, persist_on_failure

from .celery import app


@app.task(base=persist_on_failure.PersistOnFailureTask)
def fallible_task(message=None):
    """
    Simple task to let us test retry functionality.
    """
    if message:
        raise ValueError(message)


@app.task(base=persist_on_failure.PersistOnFailureTask)
def passing_task():
    """
    This task always passes
    """
    return 5


@app.task(base=logged_task.LoggedTask)
def simple_logged_task(a, b, c):  # pylint: disable=invalid-name
    """
    This task gets logged
    """
    return a + b + c

@app.task(base=logged_task.LoggedTask)
def failing_logged_task():
    """
    This task always fails.
    """
    # This will raise a ValueError
    return int("foo")
