from django.conf import settings as django_settings


class LazySrcsetSettings:
    """
    Lazy settings are the best settings.  These can be defined in the project settings and LazySrcsetSettings will
    return settings from django.conf.settings when possible, that inlcudes any setting not defined here too.
    """

    LAZY_SRCSET_GENERATOR_ID = "lazy_srcset:srcset_image"
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
