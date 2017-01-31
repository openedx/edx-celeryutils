# -*- coding: utf-8 -*-
"""
celery_utils Django application initialization.
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class CeleryUtilsConfig(AppConfig):
    """
    Configuration for the celery_utils Django application.
    """

    name = 'celery_utils'
