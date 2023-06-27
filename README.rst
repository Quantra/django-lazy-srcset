==================
Django Lazy srcset
==================

Lazy srcset and image generation for Django. Minimum effort required. No database required.

Django Lazy srcset will create all the markup and images you need to provide responsive images via the srcset attribute.  All you need to do is install it, configure your breakpoints and use the ``{% srcset %}`` template tag.

All of the hard work (image generation and cacheing) is done by django-imagekit, by default this means images are generated just in time - lazily. Please see the `django-imagekit docs <https://django-imagekit.readthedocs.io>`_ for more info and configuration options.

SVG images are supported, they will not be converted or resized but width and height attributes are still generated.

You will also need Django and Pillow.

Installation & Usage
--------------------

Install with pip:

.. code-block:: bash

    $ pip install django-lazy-srcset

Add ``"imagekit"`` and ``"lazy_srcset"`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        "imagekit",
        "lazy_srcset",
        ...
    ]

Configure your breakpoints and stuff:

.. code-block:: python

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

For further documentation and usage examples please read the docstrings in the source code for  `lazy_srcset/templatetags/lazy_srcset.py <https://github.com/Quantra/django-lazy-srcset/blob/master/lazy_srcset/templatetags/lazy_srcset.py#L98>`_.

Currently imagekit ``SourceGroup`` has not been implemented therefore the imagekit ``generateimages`` management command will not generate images for django-lazy-srcset. If you want to pre-generate images you can ``render_to_string()`` your templates in an appropriate save method or signal.  If you are using `django-content-blocks <https://github.com/Quantra/django-content-blocks>`_ this happens on publish anyway.

Clean up of unused files created by django-lazy-srcset is down to you, if you require it at all.
