"""
Initialization of Celery subsystem.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

from celery import Celery


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

app = Celery('proj')  # pylint: disable=invalid-name

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings')
app.conf.CELERY_TASK_ALWAYS_EAGER = True

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['celery_utils', 'test_utils'])
