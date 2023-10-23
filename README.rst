edx-celeryutils
=============================

.. image:: https://img.shields.io/pypi/v/edx-celeryutils.svg
    :target: https://pypi.python.org/pypi/edx-celeryutils/
    :alt: PyPI

.. image:: https://github.com/openedx/edx-celeryutils/workflows/Python%20CI/badge.svg?branch=master
    :target: https://github.com/openedx/edx-celeryutils/actions?query=workflow%3A%22Python+CI%22
    :alt: CI

.. image:: http://codecov.io/github/edx/edx-celeryutils/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/edx-celeryutils?branch=master
    :alt: Codecov

.. image:: http://edx-celeryutils.readthedocs.io/en/latest/?badge=latest
    :target: http://edx-celeryutils.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/pypi/pyversions/edx-celeryutils.svg
    :target: https://pypi.python.org/pypi/edx-celeryutils/
    :alt: Supported Python versions

.. image:: https://img.shields.io/github/license/edx/edx-celeryutils.svg
    :target: https://github.com/openedx/edx-celeryutils/blob/master/LICENSE.txt
    :alt: License

Code to support working with Celery, a distributed task queue.

Overview (please modify)
------------------------

This package contains utilities to wrap tasks with logging and to
persist them if they fail.

It also supports Django administration for searching and deleting
failed tasks, and management commands for rerunning failed tasks and
deleting old ones.

Documentation
-------------

(TODO: `Set up documentation <https://openedx.atlassian.net/wiki/spaces/DOC/pages/21627535/Publish+Documentation+on+Read+the+Docs>`_)

Publishing a Release
--------------------

After a PR merges, a new version of the package will automatically be released by Travis when the commit is tagged. Use::

    git tag -a X.Y.Z -m "Releasing version X.Y.Z"
    git push origin X.Y.Z

Do **not** create a Github Release, or ensure its message points to the CHANGELOG.rst.

License
-------

The code in this repository is licensed under the Apache 2.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/openedx/.github/blob/master/CONTRIBUTING.md>`_ for details.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@openedx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help
