#!/bin/sh
coverage run --branch --include="*feincms*" ./manage.py test feincms
