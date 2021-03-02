Django DAL
============

.. image:: https://img.shields.io/github/issues/MPASolutions/django-dal.svg
    :target: https://github.com/MPASolutions/django-dal/issues
    :alt: Issues

.. image:: https://img.shields.io/pypi/pyversions/django-dal.svg
    :target: https://img.shields.io/pypi/pyversions/django-dal.svg
    :alt: Py versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://raw.githubusercontent.com/MPASolutions/django-dal/master/LICENSE
    :alt: License


Documentation
-------------

The full documentation is at https://django-dal.readthedocs.io.


Quickstart
----------

Install Django DAL:

.. code-block:: bash

    $ pip install django-dal

Add ``django-dal`` to your ``INSTALLED_APPS``

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'django_dal',
        # ...
    ]


Running Tests
-------------

Does the code actually work?

.. code-block:: bash

    $ source <YOURVIRTUALENV>/bin/activate
    $ (myenv) $ pip install tox
    $ (myenv) $ tox


Contributors
------------

Here is a list of Django-DAL's contributors.

.. image:: https://contributors-img.web.app/image?repo=MPASolutions/django-dal
    :target: https://github.com/MPASolutions/django-dal/graphs/contributors
    :alt: Contributors
