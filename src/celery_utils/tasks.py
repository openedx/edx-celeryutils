"""
Celery tasks that support the utils in this module.
"""

from django.utils.timezone import now

from celery import shared_task


@shared_task
def mark_resolved(task_id):
    """
    Mark the specified task as resolved in the FailedTask table.

    If more than one record exists with the specified task id, they will all be
    marked resolved.
    """
    from . import models  # pylint: disable=import-outside-toplevel
    models.FailedTask.objects.filter(task_id=task_id, datetime_resolved=None).update(datetime_resolved=now())
