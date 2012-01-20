#!/bin/sh
#
# This script downloads all the software needed to run FeinCMS
#

echo "Downloading Django and django-mptt via git... (this will take some time)"

mkdir lib
cd lib
git clone git://github.com/django/django.git
git clone git://github.com/django-mptt/django-mptt.git
cd ..
ln -s lib/django/django django
ln -s lib/django-mptt/mptt mptt

cat <<EOD
Everything should be ready now. Type the following commands into the shell
to start the test server:

cd example
python manage.py runserver

Navigate to http://127.0.0.1:8000/admin/ to see the admin interface. The
username is 'admin', the password 'password'. You are probably most
interested in the page module.
EOD
