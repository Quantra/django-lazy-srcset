"""
Minimal settings
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "0m9pl2d0n7te11ne1"

DEBUG = True

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "imagekit",
    "lazy_srcset",
    "example.example_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "example.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "example" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "example" / "images"

STATIC_URL = "/static/"
STATICFILES_DIRS = [str(MEDIA_ROOT)]

IMAGEKIT_CACHEFILE_DIR = "output"
IMAGEKIT_SPEC_CACHEFILE_NAMER = "imagekit.cachefiles.namers.source_name_dot_hash"

if DEBUG:
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
        "127.0.0.1",
        "10.0.2.2",
    ]
