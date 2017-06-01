"""
Improved logging for celery tasks.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

from celery import Task


log = logging.getLogger(__name__)


# pylint: disable=abstract-method
class LoggedTask(Task):
    """
    Task base class that emits a log statement when it gets submitted.
    """

    abstract = True

    def apply_async(self, args=None, kwargs=None, **options):  # pylint: disable=arguments-differ
        """
        Emit a log statement when the task is submitted.
        """
        result = super(LoggedTask, self).apply_async(args=args, kwargs=kwargs, **options)
        log.info('Task {}[{}] submitted with arguments {}, {}'.format(
            self.name,
            result.id,
            args,
            kwargs
        ))
        return result

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Capture the exception that caused the task to be retried, if any.
        """
        super(LoggedTask, self).on_retry(exc, task_id, args, kwargs, einfo)
        if exc is not None:
            log.warning('[{}] retried due to {}'.format(task_id, einfo.traceback))
