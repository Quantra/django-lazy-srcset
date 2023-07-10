from django.conf import settings as django_settings


class LazySrcsetSettings:
    """
    Lazy settings are the best settings.  These can be defined in the project settings and LazySrcsetSettings will
    return settings from django.conf.settings when possible, that inlcudes any setting not defined here too.
    """

    # When disabled src, width and height attributes are returned so images still work but no srcset or image
    # generation will happen. By default, lazy-srcset is disabled when debug is True.
    LAZY_SRCSET_ENABLED = not django_settings.DEBUG

    # The default threshold to use when not specified in the config.
    LAZY_SRCSET_THRESHOLD = 69

    # The default generator to use when not specified in the config.
    LAZY_SRCSET_GENERATOR_ID = "lazy_srcset:srcset_image"

    # Configs
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
            # The difference in width (px) required to generate a new image
            # This prevents images being created which are too similar in size
            # If threshold is not provided LAZY_SRCSET_THRESHOLD is used
            "threshold": LAZY_SRCSET_THRESHOLD,
            # If generator_id is not provided LAZY_SRCSET_GENERATOR_ID is used
            "generator_id": LAZY_SRCSET_GENERATOR_ID,
        }
    }

    def __getattribute__(self, item):
        try:
            return getattr(django_settings, item)
        except AttributeError:
            return super().__getattribute__(item)


settings = LazySrcsetSettings()
