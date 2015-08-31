#!/usr/bin/env python

from io import open
import os
from setuptools import setup, find_packages


def read(filename):
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path, encoding='utf-8') as handle:
        return handle.read()


setup(
    name='FeinCMS',
    version=__import__('feincms').__version__,
    description='Django-based Page CMS and CMS building toolkit.',
    long_description=read('README.rst'),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/feincms/feincms/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=find_packages(
        exclude=['tests']
    ),
    package_data={
        '': ['*.html', '*.txt'],
        'feincms': [
            'locale/*/*/*.*',
            'static/feincms/*.*',
            'static/feincms/*/*.*',
            'templates/*.*',
            'templates/*/*.*',
            'templates/*/*/*.*',
            'templates/*/*/*/*.*',
            'templates/*/*/*/*/*.*',
        ],
    },
    install_requires=[
        'Django>=1.6',
        'django-mptt>=0.7.1',
        'Pillow>=2.0.0',
        'pytz>=2014.10',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    zip_safe=False,
)
