from __future__ import absolute_import, unicode_literals

import django
import os

SITE_ID = 1

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "feincms",
    "feincms.module.medialibrary",
    "feincms.module.page",
    "mptt",
    "testapp",
]

MEDIA_URL = "/media/"
STATIC_URL = "/static/"
BASEDIR = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(BASEDIR, "media/")
STATIC_ROOT = os.path.join(BASEDIR, "static/")
SECRET_KEY = "supersikret"
USE_TZ = True

ROOT_URLCONF = "testapp.urls"
LANGUAGES = (("en", "English"), ("de", "German"))
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    # request context processor is needed
    "django.core.context_processors.request",
    "testapp.context_processors.test_context",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "testapp.context_processors.test_context",
            ]
        },
    }
]
MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
)

if django.VERSION < (1, 11):
    MIDDLEWARE_CLASSES = MIDDLEWARE

if (2,) <= django.VERSION < (2, 1):
    from django.utils import deprecation

    # Anything to make mptt.templatetags.mptt_admin importable
    deprecation.RemovedInDjango20Warning = deprecation.RemovedInDjango21Warning

elif django.VERSION < (3,):
    from django.utils import deprecation

    # Anything to make mptt.templatetags.mptt_admin importable
    deprecation.RemovedInDjango20Warning = deprecation.RemovedInDjango30Warning
