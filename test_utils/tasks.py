"""
Tasks used in tests
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from celery_utils import persist_on_failure

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
