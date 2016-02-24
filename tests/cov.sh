#!/bin/sh
venv/bin/coverage run --branch --include="*feincms/feincms*" ./manage.py test testapp
venv/bin/coverage html
