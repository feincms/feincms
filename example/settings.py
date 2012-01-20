# Django settings for example project.

import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'example.db')

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': DATABASE_NAME,
}}

TIME_ZONE = 'America/Chicago'

LANGUAGE_CODE = 'en-us'

SITE_ID = int(os.environ.get('SITE_ID', 1))

USE_I18N = True

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static/')
STATIC_URL = '/static/'

import django
if django.VERSION > (1, 4):
    FEINCMS_ADMIN_MEDIA = '/static/feincms/'
else:
    FEINCMS_ADMIN_MEDIA = '/feincms_media/'
    ADMIN_MEDIA_PREFIX = '/static/admin/'

SECRET_KEY = '_wn95s-apfd-442cby5m^_^ak6+5(fyn3lvnvtn7!si&o)1x^w'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
    'django.contrib.staticfiles',

    'feincms',
    'feincms.module.blog',
    'feincms.module.page',
    'feincms.module.medialibrary',
    'example',

    'mptt',
)

try:
    # see http://nedbatchelder.com/code/coverage/
    import coverage
    TEST_RUNNER = 'example.test_utils.CoverageRunner'
    COVERAGE_MODULES = [
        'feincms',
        'feincms._internal',
        'feincms.admin',
        'feincms.admin.filterspecs',
        'feincms.admin.item_editor',
        'feincms.admin.tree_editor',
        'feincms.compat',
        'feincms.content',
        'feincms.content.application',
        'feincms.content.application.models',
        'feincms.content.comments',
        'feincms.content.comments.models',
        'feincms.content.contactform',
        'feincms.content.contactform.models',
        'feincms.content.file',
        'feincms.content.file.models',
        'feincms.content.image',
        'feincms.content.image.models',
        'feincms.content.medialibrary',
        'feincms.content.medialibrary.models',
        'feincms.content.raw',
        'feincms.content.raw.models',
        'feincms.content.richtext',
        'feincms.content.richtext.models',
        'feincms.content.rss',
        'feincms.content.rss.models',
        'feincms.content.section',
        'feincms.content.section.models',
        'feincms.content.table',
        'feincms.content.table.models',
        'feincms.content.template',
        'feincms.content.template.models',
        'feincms.content.video',
        'feincms.content.video.models',
        'feincms.context_processors',
        'feincms.contrib',
        'feincms.contrib.fields',
        'feincms.contrib.tagging',
        'feincms.default_settings',
        #'feincms.management',
        #'feincms.management.checker',
        #'feincms.management.commands',
        #'feincms.management.commands.feincms_validate',
        #'feincms.management.commands.rebuild_mptt',
        #'feincms.management.commands.rebuild_mptt_direct',
        #'feincms.management.commands.update_rsscontent',
        'feincms.models',
        'feincms.module',
        'feincms.module.blog',
        'feincms.module.blog.admin',
        'feincms.module.blog.extensions',
        'feincms.module.blog.extensions.tags',
        'feincms.module.blog.extensions.translations',
        'feincms.module.blog.models',
        'feincms.module.extensions',
        'feincms.module.extensions.changedate',
        'feincms.module.extensions.ct_tracker',
        'feincms.module.extensions.featured',
        'feincms.module.extensions.seo',
        'feincms.module.medialibrary',
        'feincms.module.medialibrary.admin',
        'feincms.module.medialibrary.models',
        'feincms.module.page',
        'feincms.module.page.admin',
        'feincms.module.page.extensions',
        'feincms.module.page.extensions.datepublisher',
        'feincms.module.page.extensions.excerpt',
        'feincms.module.page.extensions.navigation',
        'feincms.module.page.extensions.relatedpages',
        'feincms.module.page.extensions.symlinks',
        'feincms.module.page.extensions.titles',
        'feincms.module.page.extensions.translations',
        'feincms.module.page.models',
        'feincms.module.page.sitemap',
        'feincms.module.page.templatetags',
        'feincms.module.page.templatetags.feincms_page_tags',
        'feincms.shortcuts',
        'feincms.templatetags',
        'feincms.templatetags.applicationcontent_tags',
        'feincms.templatetags.feincms_tags',
        'feincms.templatetags.feincms_thumbnail',
        'feincms.templatetags.fragment_tags',
        'feincms.translations',
        'feincms.urls',
        'feincms.utils',
        'feincms.utils.html',
        'feincms.utils.html.cleanse',
        'feincms.utils.html.tidy',
        'feincms.utils.templatetags',
        'feincms.views',
        'feincms.views.base',
        'feincms.views.cbv',
        'feincms.views.cbv.urls',
        'feincms.views.cbv.views',
        'feincms.views.legacy',
        'feincms.views.legacy.urls',
        'feincms.views.legacy.views',
        'feincms.views.decorators',
        'feincms.views.generic',
        'feincms.views.generic.create_update',
        'feincms.views.generic.date_based',
        'feincms.views.generic.list_detail',
        'feincms.views.generic.simple',
    ]
except ImportError:
    # run without coverage support
    pass

LANGUAGES = (
    ('en', 'English'),
    ('de', 'German'),
    )

FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS = True
