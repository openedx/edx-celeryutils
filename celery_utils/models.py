# -*- coding: utf-8 -*-
"""
Database models for celery_utils.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

from celery import current_app

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from jsonfield import JSONField
from model_utils.models import TimeStampedModel

from celery_utils import tasks

log = logging.getLogger(__name__)


@python_2_unicode_compatible
class FailedTask(TimeStampedModel):
    """
    Representation of tasks that have failed.
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
            raise TypeError('Cannot reapply a resolved task: {}'.format(self))
        log.info('Reapplying failed task: {}'.format(self))
        original_task = current_app.tasks[self.task_name]
        original_task.apply_async(
            self.args,
            self.kwargs,
            task_id=self.task_id,
            link=tasks.mark_resolved.si(self.task_id)
        )

    def __str__(self):
        return 'FailedTask: {task_name}, args={args}, kwargs={kwargs} ({resolution})'.format(
            task_name=self.task_name,
            args=self.args,
            kwargs=self.kwargs,
            resolution='not resolved' if self.datetime_resolved is None else 'resolved'
        )
