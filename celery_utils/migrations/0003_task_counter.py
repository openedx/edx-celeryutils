# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djcelery', '0001_initial'),
        ('celery_utils', '0002_backend_cleanup'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskCounter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('expected', models.IntegerField(default=0)),
                ('locked', models.BooleanField(default=True)),
                ('completed_subtasks', models.ManyToManyField(to='djcelery.TaskMeta')),
            ],
        ),
    ]
