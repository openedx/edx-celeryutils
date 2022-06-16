"""
Database models for celery_utils.
"""

import logging

from django.db import models

from celery import current_app
from jsonfield import JSONField
from model_utils.models import TimeStampedModel

from celery_utils import tasks

log = logging.getLogger(__name__)


class FailedTask(TimeStampedModel):
    """
    Representation of tasks that have failed.

    .. pii::
       Stores arbitrary task parameters, which theoretically could include
       email addresses, although as of May 2020 does not seem to.
       Old tasks can be manually deleted in the Django administration UI.
    .. pii_retirement: local_api
    .. pii_types: other
    """

    task_name = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, db_index=True)
    args = JSONField(blank=True)
    kwargs = JSONField(blank=True)
    exc = models.CharField(max_length=255)
    datetime_resolved = models.DateTimeField(blank=True, null=True, default=None, db_index=True)

    class Meta:
        """
        To specify any metadata for FailedTask model.
        """

        index_together = [
            ('task_name', 'exc'),
        ]

    def reapply(self):
        """
        Enqueue new celery task with the same arguments as the failed task.
        """
        if self.datetime_resolved is not None:
            raise TypeError(f'Cannot reapply a resolved task: {self}')
        log.info('Reapplying failed task: {}'.format(self))
        original_task = current_app.tasks[self.task_name]
        original_task.apply_async(
            self.args,
            self.kwargs,
            task_id=self.task_id,
            link=tasks.mark_resolved.si(self.task_id)
        )

    def __str__(self):
        return f"FailedTask: {self.task_name}, " \
               f"args={self.args}, kwargs={self.kwargs} " \
               f"({'not resolved' if self.datetime_resolved is None else 'resolved'})"
