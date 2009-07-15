#!/bin/sh
# 
# This script downloads all the software needed to run FeinCMS
#

echo "Downloading Django and django-mptt via subversion... (this will take some time)"

svn checkout http://code.djangoproject.com/svn/django/trunk/django django > /dev/null
svn checkout http://django-mptt.googlecode.com/svn/trunk/mptt mptt > /dev/null

cat <<EOD
Everything should be ready now. Type the following commands into the shell
to start the test server:

cd example
python manage.py runserver

Navigate to http://127.0.0.1:8000/admin/ to see the admin interface. The
username is 'admin', the password 'password'. You are probably most
interested in the page module.
EOD
