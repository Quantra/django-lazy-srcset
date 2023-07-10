|package version|
|license|
|pypi status|
|coverage|

|python versions supported|
|django versions supported|

|code style black|
|pypi downloads|
|github stars|

==================
Django Lazy srcset
==================

Lazy srcset and image generation for Django. Minimum effort required. No database required.

Django Lazy srcset will create all the markup and images you need to provide responsive images via the srcset attribute.  All you need to do is install it, configure your breakpoints and use the ``{% srcset %}`` template tag.

All of the hard work (image generation and cacheing) is done by django-imagekit, by default this means images are generated just in time - lazily. Please see the `django-imagekit docs <https://django-imagekit.readthedocs.io>`_ for more info and configuration options.

SVG images are supported, they will not be converted or resized but width and height attributes are still added as well as the ``role="img"`` attribute.

You will also need Django and Pillow.

Installation & Usage
--------------------

Install with pip:

.. code-block:: bash

    $ pip install django-lazy-srcset

Add ``"imagekit"`` and ``"lazy_srcset"`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "imagekit",
        "lazy_srcset",
        # ...
    ]

Configure your breakpoints and stuff:

.. code-block:: python

    # Lazy srcset is disabled when DEBUG = True by default. Only set this if you want to alter that behaviour.
    LAZY_SRCSET_ENABLED = not DEBUG

    # Multiple configurations can be set and used. This is the default.
    LAZY_SRCSET = {
        "default": {
            # breakpoints is the only setting you must define
            "breakpoints": [1920, 1580, 1280, 1024, 640],
            # If max_width is not provided the source image width is used, it's a good idea to set this
            "max_width": 2560,
            # If quality is not provided PIL will choose a default
            "quality": 91,
            # If format is not provided the source image format is used
            "format": "WEBP",
        }
    }

Use the ``{% srcset %}`` template tag:

.. code-block:: django

    {% load lazy_srcset %}

    {# image is probably an ImageField #}
    <img {% srcset image %} alt="Lovely and lazy" />

    {# You can also provide relative image widths e.g. for a 4 - 3 - 2 - 1 col degradation: #}
    <img {% srcset image 25 33 50 %}  />

    {# You can provide a path to a static file #}
    <img {% srcset 'path/to/my/image.png' %} />

Whilst not required it is advisable to take a nap at this stage.

For further documentation and usage examples please read the docstrings in the source code for  `lazy_srcset/templatetags/lazy_srcset.py <https://github.com/Quantra/django-lazy-srcset/blob/master/lazy_srcset/templatetags/lazy_srcset.py>`_.

Due to the awesomeness of imagekit it's possible to configure django-lazy-srcset to use any image generator you have registered on a per config basis. Take a look at `lazy_srcset/conf.py <https://github.com/Quantra/django-lazy-srcset/blob/master/lazy_srcset/conf.py>`_ to see how to change the ``generator_id`` setting. For an example image generator look at `lazy_srcset/imagegenerators.py <https://github.com/Quantra/django-lazy-srcset/blob/master/lazy_srcset/imagegenerators.py>`_. This is completely optional.

Currently imagekit ``SourceGroup`` has not been implemented therefore the imagekit ``generateimages`` management command will not generate images for django-lazy-srcset. If you want to pre-generate images you can ``render_to_string()`` your templates in an appropriate save method or signal.  If you are using `django-content-blocks <https://github.com/Quantra/django-content-blocks>`_ this happens on publish anyway.

Clean up of unused files created by django-lazy-srcset is down to you, if you require it at all.

.. shields.io badges

.. |package version| image:: https://img.shields.io/pypi/v/django-lazy-srcset
    :alt: PyPI Package Version
    :target: https://pypi.python.org/pypi/django-lazy-srcset/

.. |python versions supported| image:: https://img.shields.io/pypi/pyversions/django-lazy-srcset
    :alt: Python Versions Supported
    :target: https://pypi.python.org/pypi/django-lazy-srcset/

.. |django versions supported| image:: https://img.shields.io/pypi/frameworkversions/django/django-lazy-srcset
    :alt: Django Versions Supported
    :target: https://pypi.python.org/pypi/django-lazy-srcset/

.. |coverage| image:: https://img.shields.io/badge/dynamic/xml?color=success&label=coverage&query=round%28%2F%2Fcoverage%2F%40line-rate%20%2A%20100%29&suffix=%25&url=https%3A%2F%2Fraw.githubusercontent.com%2FQuantra%2Fdjango-lazy-srcset%2Fmaster%2Fcoverage.xml
    :alt: Test Coverage
    :target: https://github.com/Quantra/django-lazy-srcset/blob/master/coverage.xml

.. |code style black| image:: https://img.shields.io/badge/code%20style-black-black
    :alt: Code Style Black
    :target: https://github.com/psf/black

.. |license| image:: https://img.shields.io/github/license/Quantra/django-lazy-srcset
    :alt: MIT License
    :target: https://github.com/Quantra/django-lazy-srcset/blob/master/LICENSE

.. |github stars| image:: https://img.shields.io/github/stars/Quantra/django-lazy-srcset?style=social
    :alt: GitHub Repo Stars
    :target: https://github.com/Quantra/django-lazy-srcset/stargazers

.. |pypi downloads| image:: https://img.shields.io/pypi/dm/django-lazy-srcset
    :alt: PyPI Downloads
    :target: https://pypi.python.org/pypi/django-lazy-srcset/

.. |pypi status| image:: https://img.shields.io/pypi/status/django-lazy-srcset
    :alt: PyPI Status
    :target: https://pypi.python.org/pypi/django-lazy-srcset/
