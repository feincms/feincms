# Django settings for example project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'example.db'

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = True

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'
FEINCMS_ADMIN_MEDIA = '/feincms_media/'

SECRET_KEY = '_wn95s-apfd-442cby5m^_^ak6+5(fyn3lvnvtn7!si&o)1x^w'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'example.urls'

TEMPLATE_DIRS = (
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

    'django.contrib.admin',
    'feincms',
    'feincms.module.blog',
    'feincms.module.page',
    'feincms.module.medialibrary',
    'example',

    'mptt',
)


COVERAGE_MODULES = ['feincms.admin.editor',
                    'feincms.admin.item_editor',
                    'feincms.admin.tree_editor',
                    'feincms.content.application.models',
                    'feincms.content.contactform.models',
                    'feincms.content.file.models',
                    'feincms.content.image.models',
                    'feincms.content.medialibrary.models',
                    'feincms.content.raw.models',
                    'feincms.content.richtext.models',
                    'feincms.content.rss.models',
                    'feincms.content.video.models',
                    'feincms.models',
                    'feincms.module.blog.admin',
                    'feincms.module.blog.extensions.seo',
                    #'feincms.module.blog.extensions.tags', # I don't have tagging installed here...
                    'feincms.module.blog.extensions.translations',
                    'feincms.module.blog.models',
                    'feincms.module.medialibrary.admin',
                    'feincms.module.medialibrary.models',
                    'feincms.module.page.admin',
                    'feincms.module.page.extensions.changedate',
                    'feincms.module.page.extensions.datepublisher',
                    'feincms.module.page.extensions.navigation',
                    'feincms.module.page.extensions.seo',
                    'feincms.module.page.extensions.symlinks',
                    'feincms.module.page.extensions.titles',
                    'feincms.module.page.extensions.translations',
                    'feincms.module.page.models',
                    'feincms.module.page.templatetags.feincms_page_tags',
                    'feincms.settings',
                    'feincms.templatetags.applicationcontent_tags',
                    'feincms.templatetags.feincms_tags',
                    'feincms.translations',
                    'feincms.utils',
                    'feincms.views.applicationcontent',
                    'feincms.views.base',
                    ]

try:
    # see http://nedbatchelder.com/code/coverage/
    import coverage
    TEST_RUNNER = 'example.test_utils.test_runner_with_coverage'
except ImportError:
    # run without coverage support
    pass

LANGUAGES = (
    ('en', 'English'),
    ('de', 'German'),
    )
