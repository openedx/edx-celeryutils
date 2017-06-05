# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import management
from django.db import migrations, models


def forwards(apps, schema_editor):
    """
    A dirty, dirty hack to clean up the unused (for us) djcelery tables.
    """
    if not Migration.DIRTY_HACK_CONSTANT:
        Migration.DIRTY_HACK_CONSTANT = True
        management.call_command('migrate', 'djcelery', '--fake-initial')
        management.call_command('migrate', 'djcelery', 'zero')


class Migration(migrations.Migration):

    DIRTY_HACK_CONSTANT = False
    dependencies = [
        ('celery_utils', '0001_initial'),
    ]

    run_before = [
        ('djcelery', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop),
    ]
