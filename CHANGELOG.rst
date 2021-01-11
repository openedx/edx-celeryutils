Change Log
----------

..
   All enhancements and patches to edx-celeryutils will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~
*

[1.0.0] - 2021-01-21
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Dropped python3.5 support.

[0.5.4] - 2020-12-10
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Upgrade celery to 5.0.4

[0.5.3] - 2020-09-15
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Move to Apache 2.0 license

[0.5.2] - 2020-08-28
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Upgrade celery to 4.2.2

[0.5.1] - 2020-06-30
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Added python38 support.

[0.5.0] - 2020-04-01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* No functional change.

[0.4.0] - 2020-03-05
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Removed all references to django-celery and removed it as a dependency.
* Removed ChordableDjangoBackend and ChordData.

[0.2.7] - 2017-12-04
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add logging for non-retried failed tasks.

[0.2.6] - 2017-08-07
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Upgrade version of django-celery.

[0.2.5] - 2017-08-03
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Django 1.11 compatibility

[0.2.4] - 2017-06-20
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add management command to fix djcelery tables.

[0.2.1] - 2017-05-22
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add ChordableDjangoBackend and testing.

[0.1.3] - 2017-03-01
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Packaging changes.

[0.1.1] - 2017-02-22
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Added django admin for management of FailedTasks.

[0.1.0] - 2017-01-31
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initial release

Contains two task base classes:

* LoggedTask - Reports extra logging info 1) when a task is submitted to the task service (for tracking task latency) and 2) when the task retries, it surfaces information about the raised exception.
* PersistOnFailureTask - Stores a record of failed tasks that can later be retried.
