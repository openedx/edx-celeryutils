"""
Celery utility code for persistent tasks.
"""
# pylint: disable=abstract-method


from celery import Task

from .logged_task import LoggedTask
from .models import FailedTask


class PersistOnFailureTask(Task):
    """
    Custom Celery Task base class that persists task data on failure.
    """

    abstract = True
    typing = False

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the task fails, persist a record of the task.
        """
        if not FailedTask.objects.filter(task_id=task_id, datetime_resolved=None).exists():
            FailedTask.objects.create(
                task_name=_truncate_to_field(FailedTask, 'task_name', self.name),
                task_id=task_id,  # Fixed length UUID: No need to truncate
                args=args,
                kwargs=kwargs,
                # TODO: Remove ".replace(',', ''))" when python 3.5 support is dropped
                exc=_truncate_to_field(FailedTask, 'exc', repr(exc).replace(',', '')),
            )
        super().on_failure(exc, task_id, args, kwargs, einfo)


class LoggedPersistOnFailureTask(PersistOnFailureTask, LoggedTask):
    """
    Provides persistence features, as well as logging of task invocation.
    """

    abstract = True


def _truncate_to_field(model, field_name, value):
    """
    Shorten data to fit in the specified model field.

    If the data were too big for the field, it would cause a failure to
    insert, so we shorten it, truncating in the middle (because
    valuable information often shows up at the end.
    """
    field = model._meta.get_field(field_name)  # pylint: disable=protected-access
    if len(value) > field.max_length:
        midpoint = field.max_length // 2
        len_after_midpoint = field.max_length - midpoint
        first = value[:midpoint]
        sep = '...'
        last = value[len(value) - len_after_midpoint + len(sep):]
        value = sep.join([first, last])
    return value
