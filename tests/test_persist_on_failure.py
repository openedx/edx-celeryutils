"""
Testing persistent tasks

Tasks built with the FailedTask base class are imported from test_utils.tasks.
  * fallible_task - Can fail if passed a failure `message` argument.
  * passing_task - Always passes when run.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import six

from celery_utils.models import FailedTask
from test_utils import tasks


@pytest.mark.django_db
def test_fallible_task_without_failure():
    result = tasks.fallible_task.delay()
    result.wait()
    assert result.status == 'SUCCESS'
    assert not FailedTask.objects.exists()


@pytest.mark.django_db
def test_fallible_task_with_failure():
    result = tasks.fallible_task.delay(message='The example task failed')
    with pytest.raises(ValueError):
        result.wait()
    assert result.status == 'FAILURE'
    failed_task_object = FailedTask.objects.get()
    # Assert that we get the kind of data we expect
    assert failed_task_object.task_name == tasks.fallible_task.name
    assert failed_task_object.args == []
    assert failed_task_object.kwargs == {'message': 'The example task failed'}
    if six.PY2:
        assert failed_task_object.exc == "ValueError(u'The example task failed',)"
    else:
        assert failed_task_object.exc == "ValueError('The example task failed',)"
    assert failed_task_object.datetime_resolved is None


@pytest.mark.django_db
def test_persists_when_called_with_wrong_args():
    result = tasks.fallible_task.delay(15, '2001-03-04', err=True)
    with pytest.raises(TypeError):
        result.wait()
    assert result.status == 'FAILURE'
    failed_task_object = FailedTask.objects.get()
    assert failed_task_object.args == [15, '2001-03-04']
    assert failed_task_object.kwargs == {'err': True}


@pytest.mark.django_db
def test_persists_with_overlength_field():
    overlong_message = ''.join('%03d' % x for x in six.moves.range(100))
    result = tasks.fallible_task.delay(message=overlong_message)
    with pytest.raises(ValueError):
        result.wait()
    failed_task_object = FailedTask.objects.get()
    # Length is max field length
    assert len(failed_task_object.exc) == 255
    # Ellipses are put in the middle
    if six.PY2:
        # Ellipses offset by one due to the u' in the ValueError
        assert failed_task_object.exc.startswith("ValueError(u'")
        assert failed_task_object.exc[124:133] == '037...590'
    else:
        assert failed_task_object.exc.startswith("ValueError('")
        assert failed_task_object.exc[124:133] == '370...590'
    # The beginning of the input is captured
    # The end of the input is captured
    assert failed_task_object.exc[-9:] == "098099',)"


@pytest.mark.django_db
def test_cannot_reapply_resolved_task():
    failed_task = FailedTask.objects.create(
        task_name=tasks.fallible_task.name,
        task_id='will_succeed',
        args=[],
        kwargs={},
    )
    failed_task.reapply()
    failed_task = FailedTask.objects.get(pk=failed_task.pk)
    assert failed_task.datetime_resolved is not None
    with pytest.raises(TypeError):
        failed_task.reapply()
