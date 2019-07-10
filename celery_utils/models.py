# -*- coding: utf-8 -*-
"""
Database models for celery_utils.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime
import json
import logging
from traceback import format_exc

from celery import current_app
from celery.canvas import Signature
from celery.exceptions import ChordError
from celery.states import FAILURE, READY_STATES, SUCCESS
from djcelery.models import TaskMeta

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

    class Meta(object):
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


@python_2_unicode_compatible
class ChordData(models.Model):
    """
    Data model that allows chord synchronization via ChordableDjangoBackend.

    Consumers of the ChordableDjangoBackend should not need to explicitly use
    these models at all, they're designed to be used under the covers.
    """

    completed_results = models.ManyToManyField(TaskMeta, related_name='chorddata_sub_results')
    serialized_callback = models.TextField()  # A frozen, serialized callback signature
    callback_result = models.OneToOneField(TaskMeta, related_name='chorddata_callback_result')

    def __str__(self):
        return "{} depends on {} subtasks, status {}".format(
            self.callback_result.task_id,
            self.completed_results.count(),
            self.callback_result.status
        )

    def is_ready(self):
        """
        Check to see if all subtasks are in a finished state.
        """
        return all(result.status in READY_STATES for result in self.completed_results.all())

    def execute_callback(self):
        """
        Execute serialized callback. Called via on_chord_part_return.

        There are no parameters, as everything we need is already serialized
        in the model somewhere.
        """
        callback_signature = Signature.from_dict(json.loads(self.serialized_callback))

        if any(result.status == FAILURE for result in self.completed_results.all()):
            # we either remove the failures and only return results from successful subtasks, or fail the entire chord
            if callback_signature.get('options', {}).get('propagate', current_app.conf.CELERY_CHORD_PROPAGATES):
                try:
                    raise ChordError(
                        "Error in subtasks! Ids: {}".format([
                            result.task_id
                            for result in self.completed_results.all()
                            if result.status == FAILURE
                        ])
                    )
                except ChordError as error:
                    self.mark_error(error, is_subtask=True)
                    return
            else:
                """
                Dev note: this doesn't *quite* match the behavior of the default backend.

                According to http://www.pythondoc.com/celery-3.1.11/configuration.html#celery-chord-propagates,
                the 2 options are to either propagate through (as done above), or to forward the Exception result
                into callback (versus this approach of dropping error results). It seems silly to ask callbacks to
                expect exception results as input though, so we drop them.
                """  # pylint: disable=pointless-string-statement
                for result in self.completed_results.all():
                    if result.status == FAILURE:
                        self.completed_results.remove(result)  # pylint: disable=no-member
                        result.delete()

        if callback_signature.get('options', {}).get('use_iterator', True):
            # If we're using an iterator, it's assumed to be because there are size concerns with the results
            # Thus, the callback_result TaskMeta object will have a null 'result' in the database, because you
            # stored those results someplace else as part of the callback function, right?
            try:
                callback_signature(self.completed_results.values_list('result', flat=True).iterator)
            except Exception as error:  # pylint: disable=broad-except
                self.mark_error(error, is_subtask=False)
                return
            else:
                self.callback_result.status = SUCCESS
                self.callback_result.date_done = datetime.now()
                self.callback_result.save()
        else:
            results_list = [subtask.result for subtask in self.completed_results.all()]
            callback_signature.id = self.callback_result.task_id
            callback_signature.apply_async((results_list, ), {})

    def mark_error(self, error, is_subtask):
        """
        Mark this ChordData's callback_result as a failure, and log it.

        Intended to be called in an exception handler, to make use of
        format_exc().
        """
        self.callback_result.traceback = format_exc()
        self.callback_result.status = FAILURE
        self.callback_result.result = error
        self.callback_result.date_done = datetime.now()
        self.callback_result.save()
        noun = "subtask" if is_subtask else "callback"
        log.error(
            'ChordData {} failure: {}'.format(noun, self.callback_result.traceback)
        )
