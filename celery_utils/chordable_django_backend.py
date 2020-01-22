u"""
An opt-in backend, designed to make using chords with the Django ORM easy.

Additionally avoids the pooling unlock used by default in django-celery for
performance benfits.

Usage
-----
    First, import the needful from this module:
        from celeryutils.chordable_django_backend import chord, chord_task

    Then, change the task() decorators on your functions to the new chord_
    decorators:
        # Note that standard task options will be passed though!
        @chord_task(max_retries=2, default_retry_delay=10)
        def add(x, y):
            return x + y

        @chord_task()
        def tsum(results):
            _sum = 0
            for num in results:
                _sum = _sum + num
            return _sum

    Finally, call chord() as you normally would, and let ChordableDjangoBackend
    take care of the rest:
        chord(add.s(i, i) for i in xrange(10))(tsum.s())

Notes
-----
    Please ensure that your callback function stores its results somewhere.
    There is no "chord finished, come and get it!" signal, so having the
    callback store the synthesized results of your parallel subtasks is
    crucial.

    By default, errors in the subtasks will prevent the callback from running.
    Instead, the callback result will be set to FAILURE status and the result
    will contain an exception detailing which subtasks errored. The other option
    is <TODO FIGURE OUT THE DEV NOTE IN MODELS.PY AND PUT RESULTS HERE>, which
    can be set with a False use_iterator option on your callback signature.

    Similarly, the callback is, by default, called with an iterator of subtask
    results. Since this cannot be serialized, it cannot be launched
    asynchronously, and the final subtask will execute the callback in-process.
    In order to disable this behavior (and build the results list in-memory),
    set the propagate option on your callback signature to False.

    To set either of the use_iterator or propagate options, add them to your
    callback signature as follows:
        c = chord(add.s(i, i) for i in xrange(10))
        t = tsum.s()
        t.options = {
            'propagate': False,
            'use_iterator': False
        }
        c(t)

"""
from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy
from datetime import datetime, timedelta
import json

from celery import chord as _chord
from celery import current_app, task
from celery.states import FAILURE, SUCCESS
from djcelery.backends.database import DatabaseBackend
from djcelery.models import TaskMeta

from django.db import transaction

from celery_utils.models import ChordData


class chord(_chord):  # pylint: disable=invalid-name
    u"""
    Overrides the default celery chord primitive to use this backend.
    """

    def __init__(self, *args, **kwargs):
        u"""Super init, with a specialized 'app' kwarg."""
        given_app = kwargs.pop(u'app', current_app)
        kwargs[u'app'] = ChordableDjangoBackend.get_suitable_app(given_app)
        super(chord, self).__init__(*args, **kwargs)


def chord_task(*args, **kwargs):
    u"""
    Override of the default task decorator to specify use of this backend.
    """
    given_backend = kwargs.get(u'backend', None)
    if not isinstance(given_backend, ChordableDjangoBackend):
        kwargs[u'backend'] = ChordableDjangoBackend(kwargs.get('app', current_app))
    return task(*args, **kwargs)


class ChordableDjangoBackend(DatabaseBackend):
    u"""
    Extends djcelery.backends.database:DatabaseBackend to avoid polling.

    See usage notes in module docstring before using.

    Celery 4 upgrade notes
    ----------------------
        - django-celery (djcelery) is needed for ChordableDjangoBackend, and it's
            incompatible with celery 4. Upon upgrading, we'll need to switch the
            base class from djcelery.backends.database:DatabaseBackend to
            django-celery-results.backends.database:DatabaseBackend
    """

    def _cleanup(self, status, expires_multiplier=1):
        u"""
        Clean up expired records.

        Will remove all entries for any ChordData whose callback result is in
        state <status> that was marked completed more than
        (self.expires * <expires_multipler>) ago.
        """
        # self.expires is inherited, and defaults to 1 day (or setting CELERY_TASK_RESULT_EXPIRES)
        expires = self.expires if isinstance(self.expires, timedelta) else timedelta(seconds=self.expires)
        expires = expires * expires_multiplier
        chords_to_delete = ChordData.objects.filter(
            callback_result__date_done__lte=datetime.now() - expires,
            callback_result__status=status
        ).iterator()
        for _chord in chords_to_delete:
            subtask_ids = [subtask.task_id for subtask in _chord.completed_results.all()]
            _chord.completed_results.clear()
            TaskMeta.objects.filter(task_id__in=subtask_ids).delete()                   # pylint: disable=no-member
            _chord.callback_result.delete()
            _chord.delete()

    def cleanup(self):
        u"""
        Override default implementation of celery.task.backend_cleanup task.

        We run this task on every callback execution, it could also easily be
        run using a celery beat worker.
        """
        self._cleanup(SUCCESS)
        self._cleanup(FAILURE, expires_multiplier=10)  # Let failed records stick around a bit longer

    def add_to_chord(self, group_id, result):  # pragma: no cover
        u"""
        Deliberate override of abstract base method. We don't do anything here.
        """

    def on_chord_part_return(self, task, state, result, propagate=False):  # pylint: disable=redefined-outer-name
        """
        Update the linking ChordData object and execute callback if needed.

        Args:
        ----
            task: The task that just finished executing. Most useful values are stored on task.request.
            state: the status of the just-finished task.
            result: the resulting value of task execution.
            propagate: unused here, we check CELERY_CHORD_PROPAGATES and the
                chord's options in chord_data.execute_callback().

        """
        with transaction.atomic():
            chord_data = ChordData.objects.select_for_update().get(  # select_for_update will prevent race conditions
                callback_result__task_id=task.request.chord[u'options'][u'task_id']
            )
            _ = TaskMeta.objects.update_or_create(
                task_id=task.request.id,
                defaults={
                    u'status': state,
                    u'result': result
                }
            )
            if chord_data.is_ready():
                # we don't use celery beat, so this is as good a place as any to fire off periodic cleanup tasks
                self.get_suitable_app(current_app).tasks[u'celery.backend_cleanup'].apply_async()
                chord_data.execute_callback()

    def apply_chord(self, header, partial_args, group_id, body, **options):
        """
        Instantiate a linking ChordData object before executing subtasks.

        Args:
        ----
            header: a list of incomplete subtask signatures, with partial
                different-per-instance arguments already set.
            partial_args: list of same-per-instance subtask arguments.
            group_id: a uuid that proved unnecessary in our approach. We use
                the callback's frozen TaskMeta id as a linking piece of data.
            body: the callback task signature, with all non-subtask-dependent
                arguments already set.

        Return value is the (unfinished) AsyncResult for body.

        """
        callback_entry = TaskMeta.objects.create(task_id=body.id)
        chord_data = ChordData.objects.create(callback_result=callback_entry)
        for subtask in header:
            subtask_entry = TaskMeta.objects.create(task_id=subtask.id)
            chord_data.completed_results.add(subtask_entry)
        if body.options.get(u'use_iterator', None) is None:
            body.options[u'use_iterator'] = True
        chord_data.serialized_callback = json.dumps(body)
        chord_data.save()

        return header(*partial_args, task_id=group_id)

    def fallback_chord_unlock(self, group_id, body, result=None, countdown=1, **kwargs):  # pragma: no cover
        u"""
        Deliberate pass override.

        The default django-celery DatabaseBackend will use this method to cry
        havoc, and let slip the dogs of repeats-every-second polling. We do not
        want that to happen, and so override the method to do nothing.
        """

    @classmethod
    def get_suitable_app(cls, given_app):
        u"""
        Return a clone of given_app with ChordableDjangoBackend, if needed.
        """
        if not isinstance(getattr(given_app, 'backend', None), ChordableDjangoBackend):
            return_app = deepcopy(given_app)
            return_app.backend = ChordableDjangoBackend(return_app)
            return return_app
        return given_app
