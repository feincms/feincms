#!/usr/bin/env python

from distutils.core import setup
import os
import setuplib

packages, data_files = setuplib.find_files('feincms')

setup(name='FeinCMS',
    version=__import__('feincms').__version__,
    description='Django-based Page CMS and CMS building toolkit.',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Matthias Kestenholz',
    author_email='mk@feinheit.ch',
    url='http://github.com/feincms/feincms/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=packages,
    data_files=data_files,
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
)
