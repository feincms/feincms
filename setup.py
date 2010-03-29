#!/usr/bin/env python

import os
from setuptools import setup, find_packages
from setuptools.dist import Distribution

Distribution({
    "setup_requires": [
        #'Django >=1.1.1'
    ]
})

import feincms

setup(name='FeinCMS',
    version=feincms.__version__,
    description='Django-based Page CMS and CMS building toolkit.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/matthiask/feincms/',
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=[
        #'Django >=1.1.1',
    ],
    requires=[
        #'lxml', # only needed for rich text cleansing
        'tagging (>0.2.1)', # please use SVN trunk
        'django_mptt (>0.2.1)', # please use the version from http://github.com/matthiask/django-mptt/
    ],
    packages=['feincms',
        'feincms.admin',
        'feincms.content',
        'feincms.content.application',
        'feincms.content.contactform',
        'feincms.content.file',
        'feincms.content.image',
        'feincms.content.medialibrary',
        'feincms.content.raw',
        'feincms.content.richtext',
        'feincms.content.rss',
        'feincms.content.section',
        'feincms.content.table',
        'feincms.content.video',
        'feincms.contrib',
        'feincms.management',
        'feincms.management.commands',
        'feincms.module',
        'feincms.module.blog',
        'feincms.module.blog.extensions',
        'feincms.module.medialibrary',
        'feincms.module.extensions',
        'feincms.module.page',
        'feincms.module.page.extensions',
        'feincms.module.page.templatetags',
        'feincms.templatetags',
        'feincms.utils',
        'feincms.utils.html',
        'feincms.views',
        'feincms.views.generic',
    ],
    include_package_data=True,
    zip_safe=False,
)

