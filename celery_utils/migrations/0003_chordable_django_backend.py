# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celery_utils', '0002_djcelery_cleanup'),
        ('djcelery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChordData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('serialized_callback', models.TextField()),
                ('callback_result', models.OneToOneField(related_name='chorddata_callback_result', to='djcelery.TaskMeta')),
                ('completed_results', models.ManyToManyField(related_name='chorddata_sub_results', to='djcelery.TaskMeta')),
            ],
        ),
    ]
