#!/bin/sh

(
    cd .tox/py27-1.6.X
    bin/pip install -U --editable=git+git://github.com/django/django.git@stable/1.6.x#egg=django-dev
)
(
    cd .tox/py27-1.7.X
    bin/pip install -U --editable=git+git://github.com/django/django.git@master#egg=django-dev
)
(
    cd .tox/py33-1.6.X
    bin/pip install -U --editable=git+git://github.com/django/django.git@stable/1.6.x#egg=django-dev
)
(
    cd .tox/py33-1.7.X
    bin/pip install -U --editable=git+git://github.com/django/django.git@master#egg=django-dev
)
