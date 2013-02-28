#!/bin/sh
coverage run --branch --include="*feincms*" ./manage.py test testapp
coverage html
