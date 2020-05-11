edx-celeryutils
=============================

.. image:: https://img.shields.io/pypi/v/edx-celeryutils.svg
    :target: https://pypi.python.org/pypi/edx-celeryutils/
    :alt: PyPI

.. image:: https://travis-ci.org/edx/edx-celeryutils.svg?branch=master
    :target: https://travis-ci.org/edx/edx-celeryutils
    :alt: Travis

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
    :target: https://github.com/edx/edx-celeryutils/blob/master/LICENSE.txt
    :alt: License

The ``README.rst`` file should start with a brief description of the repository,
which sets it in the context of other repositories under the ``edx``
organization. It should make clear where this fits in to the overall edX
codebase.

Code to support working with celery

Overview (please modify)
------------------------

The ``README.rst`` file should then provide an overview of the code in this
repository, including the main components and useful entry points for starting
to understand the code in more detail.

Documentation
-------------

The full documentation is at https://edx-celeryutils.readthedocs.org.

Publishing a Release
--------------------

After a PR merges, a new version of the package will automatically be released by Travis when the commit is tagged. Use::

    git tag -a X.Y.Z -m "Releasing version X.Y.Z"
    git push origin X.Y.Z

Do **not** create a Github Release, or ensure its message points to the CHANGELOG.rst.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details.

Even though they were written with ``edx-platform`` in mind, the guidelines
should be followed for Open edX code in general.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help
