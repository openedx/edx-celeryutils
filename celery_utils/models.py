# -*- coding: utf-8 -*-
"""
Database models for celery_utils.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

from celery import current_app

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from djcelery.models import TaskMeta

from jsonfield import JSONField
from model_utils.models import TimeStampedModel

from . import tasks

log = logging.getLogger(__name__)


class TaskCounter(models.Model):
    """
    A naive model to track subtask completion.
    """
    expected = models.IntegerField(default=0)
    completed_subtasks = models.ManyToManyField(TaskMeta)
    locked = models.BooleanField(default=True)  # prevent callback until all subtasks have spawned

    @classmethod
    def update(cls, _id, task):
        counter = cls.objects.select_for_update().get(id=_id)
        counter.completed_subtasks.add(task)
        counter.save()

    @classmethod
    def is_finished(cls, _id):
        counter = cls.objects.get(id=_id)
        return (
            not counter.locked and
            counter.completed_subtasks.filter(state='SUCCESS').count() >= counter.expected
        )

    @classmethod
    def results_itr(cls, _id):
        counter = cls.objects.get(id=_id)
        for subtask in counter.completed_subtasks:
            yield subtask.result

    @classmethod
    def cleanup_after_callback(cls, _id):
        counter = cls.objects.get(id=_id)
        for subtask in counter.completed_subtasks:
            subtask.delete()
        counter.delete()


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

    class Meta(object):
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
