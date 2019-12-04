"""
Test ChordableDjangoBackend.

A lot of the intended usage of this backend happens asychronously, which is
notoriously hard to test. Please do extensive testing for your situation before
relying on async behavior, as these tests only ensure correctness in a single
threaded process.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from builtins import range as _range
from datetime import datetime, timedelta

from celery import current_app
from celery.exceptions import ChordError
from celery.states import FAILURE, PENDING, SUCCESS
from djcelery.models import TaskMeta
from freezegun import freeze_time
from mock import MagicMock, patch
import pytest

from django.test import override_settings

from celery_utils.chordable_django_backend import ChordableDjangoBackend, chord, chord_task
from celery_utils.models import ChordData


@chord_task()
def chord_subtask(i):
    """
    Toy example of a subtask.
    """
    return i + i


@chord_task()
def chord_callback(results):
    """
    Toy example of a callback.
    """
    return sum([result for result in results])


@chord_task()
def chord_callback_itr(results_itr):
    """
    Toy example of a callback that accepts an iterator.
    """
    return sum(result for result in results_itr())


@chord_task()
def chord_callback_no_itr(results):
    """
    Toy example of a callback that does not accept an iterator.
    """
    return sum(results)


@chord_task()
def chord_callback_error(results):  # pylint: disable=unused-argument
    """
    Toy example of a callback that raises an error.
    """
    raise NotImplementedError('Nothing was ever implemented in this task :(')


def test_overrides():
    """
    Test to ensure ChordableDjangoBackend promitives override as expected.
    """
    @chord_task()
    def inner_task1(*args):  # pylint: disable=missing-docstring, unused-argument
        pass

    @chord_task(backend=current_app.backend)
    def inner_task2(*args):  # pylint: disable=missing-docstring, unused-argument
        pass

    @chord_task(backend=ChordableDjangoBackend(current_app))
    def inner_task3(*args):  # pylint: disable=missing-docstring, unused-argument
        pass

    test_chord1 = chord(inner_task1(i) for i in _range(10))
    test_chord2 = chord((inner_task2(i) for i in _range(10)), app=current_app)
    test_chord3 = chord(
        (inner_task3(i) for i in _range(10)),
        app=ChordableDjangoBackend.get_suitable_app(current_app)
    )

    assert isinstance(inner_task1.backend, ChordableDjangoBackend)
    assert isinstance(inner_task2.backend, ChordableDjangoBackend)
    assert isinstance(inner_task3.backend, ChordableDjangoBackend)

    assert isinstance(test_chord1.app.backend, ChordableDjangoBackend)
    assert isinstance(test_chord2.app.backend, ChordableDjangoBackend)
    assert isinstance(test_chord3.app.backend, ChordableDjangoBackend)


def test_simple_chord():
    """
    Test full chord execution in eager mode, check result.
    """
    test_chord = chord(chord_subtask.s(i) for i in _range(10))(chord_callback.s())

    # [0, 1, ..., 9] + [0, 1, ..., 9] = [0, 2, 4, 6, 8, 12, 14, 16, 18]
    # 2+4+6+8+10+12+14+16+18 = 90
    assert test_chord.result == 90


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False)
def test_chord_itr():
    """
    Test a standard chord with default options.
    """
    chord_data = _test_chord_internal(chord_callback_itr.s())
    assert chord_data.callback_result.status == SUCCESS
    assert chord_data.callback_result.result is None


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False)
def test_chord_no_itr():
    """
    Test a standard chord with the use_iterator callback option set to False.
    """
    with patch('celery.app.task.Task.apply_async') as mock_apply_async:
        callback = chord_callback_no_itr.s()
        callback.options = {'use_iterator': False}
        chord_data = _test_chord_internal(callback)

        # since we've overriden CELERY_ALWAYS_EAGER, the callback will not be run synchronously
        # however, since there are no workers, it also will not be run asynchronously
        assert chord_data.callback_result.status == PENDING
        assert mock_apply_async.called


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False, CELERY_CHORD_PROPAGATES=True)
def test_failing_chord_propagate():
    """
    Test a chord with failing subtasks and propagation.
    """
    chord_data = _test_chord_internal(chord_callback_itr.s(), failing_subtasks=True)

    assert chord_data.callback_result.status == FAILURE
    assert isinstance(chord_data.callback_result.result, ChordError)
    assert chord_data.callback_result.traceback


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False, CELERY_CHORD_PROPAGATES=True)
def test_failing_chord_no_propagate():
    """
    Test a chord with failing subtasks and propagation.
    """
    callback = chord_callback_itr.s()
    callback.options = {'propagate': False}
    chord_data = _test_chord_internal(callback, failing_subtasks=True)

    assert chord_data.callback_result.result is None
    # 6 subtasks, as indices 0, 3, 6, and 9 were dropped
    assert "depends on 6 subtasks, status SUCCESS" in str(chord_data)


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False)
def test_callback_error():
    chord_data = _test_chord_internal(chord_callback_error.s())

    assert chord_data.callback_result.status == FAILURE
    assert isinstance(chord_data.callback_result.result, NotImplementedError)
    assert chord_data.callback_result.traceback
    assert chord_data.completed_results.filter(status=SUCCESS).count() == 10


def _test_chord_internal(callback_signature, failing_subtasks=False):
    """
    "Run" a chord in non-eager mode by mocking a bunch of things out.
    """
    # Notice that we don't specify an app kwargs here, the 'chord' override will handle things
    test_chord = chord(chord_subtask.s(i) for i in _range(10))(callback_signature)

    # We now have several "tasks queued for execution" that will never be executed.
    assert TaskMeta.objects.all().count() == 11  # 10 subtasks, 1 callback

    chord_data = ChordData.objects.filter(callback_result__task_id=test_chord.id).first()
    for i, subtask in enumerate(chord_data.completed_results.all()):
        subtask.status = FAILURE if i % 3 == 0 and failing_subtasks else SUCCESS
        subtask.request = MagicMock(id=subtask.task_id, chord={'options': {'task_id': test_chord.id}})
        chord_subtask.backend.on_chord_part_return(subtask, subtask.status, -2)

    return chord_data


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False)
def test_cleanup_success():
    """
    Test backend cleanup of successful ChordData usage.
    """
    _test_cleanup()


@pytest.mark.django_db
@override_settings(CELERY_ALWAYS_EAGER=False)
def test_cleanup_failure():
    """
    Test backend cleanup of failure ChordData usage.
    """
    _test_cleanup(failures=True)


def _test_cleanup(failures=False):
    """
    Validate that the celery.backend_cleanup task calls our backend.
    """
    _test_chord_internal(chord_callback_itr.s(), failing_subtasks=failures)
    cleanup = ChordableDjangoBackend.get_suitable_app(current_app).tasks['celery.backend_cleanup']

    with freeze_time(datetime.now() + timedelta(days=8)):
        cleanup.apply()
    assert TaskMeta.objects.all().count() == (11 if failures else 0)
    assert ChordData.objects.all().count() == (1 if failures else 0)

    # after 70 days we'll clean up failures too
    with freeze_time(datetime.now() + timedelta(days=71)):
        cleanup.apply()
    assert TaskMeta.objects.all().count() == 0
    assert ChordData.objects.all().count() == 0
