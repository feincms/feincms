#!/bin/sh
#
# This script downloads all the software needed to run FeinCMS
#

echo "Downloading Django and django-mptt via git... (this will take some time)"

git clone git://github.com/django/django.git django
git clone git://github.com/matthiask/django-mptt.git mptt

cat <<EOD
Everything should be ready now. Type the following commands into the shell
to start the test server:

cd example
python manage.py runserver

Navigate to http://127.0.0.1:8000/admin/ to see the admin interface. The
username is 'admin', the password 'password'. You are probably most
interested in the page module.
EOD
