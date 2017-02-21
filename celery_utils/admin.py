"""
Admin site configuration.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib import admin

from .models import FailedTask


class FailedTaskAdmin(admin.ModelAdmin):
    """
    Customized admin for the FailedTask model.
    """
    date_hierarchy = 'created'
    list_display = ['task_id', 'task_name', 'args', 'kwargs', 'created', 'datetime_resolved']
    list_filter = ['task_name']
    search_fields = ['task_name', 'task_id', 'args', 'kwargs']


admin.site.register(FailedTask, FailedTaskAdmin)
