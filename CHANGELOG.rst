Change Log
----------

..
   All enhancements and patches to cookiecutter-django-app will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
~~~~~~~~~~


Added
_____

[0.1.1] - 2017-02-22
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Added django admin for management of FailedTasks.

[0.1.0] - 2017-01-31
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initial release

Contains two task base classes:

* LoggedTask - Reports extra logging info 1) when a task is submitted to the task service (for tracking task latency) and 2) when the task retries, it surfaces information about the raised exception.
* PersistOnFailureTask - Stores a record of failed tasks that can later be retried.
