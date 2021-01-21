from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration used to have a model with a dependency on django-celery.

    All the code in this migration has been removed along with the library.
    """

    dependencies = [
        ('celery_utils', '0001_initial'),
    ]

    operations = [
    ]
