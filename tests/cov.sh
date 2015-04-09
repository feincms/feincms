#!/bin/sh
coverage run --branch --include="*feincms/feincms*" ./manage.py test testapp
coverage html
