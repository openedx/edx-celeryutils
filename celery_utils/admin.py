"""
Admin site configuration.
"""

from django.contrib import admin

from .models import FailedTask


class FailedTaskAdmin(admin.ModelAdmin):
    """
    Customized admin for the FailedTask model.
    """

    list_display = ['task_id', 'task_name', 'args', 'kwargs', 'created', 'datetime_resolved']
    list_filter = ['task_name', 'created', 'datetime_resolved']
    search_fields = ['task_name', 'task_id', 'args', 'kwargs']


admin.site.register(FailedTask, FailedTaskAdmin)
