#!/bin/sh
#
# This script downloads all the software needed to run FeinCMS
#

cd example
virtualenv venv
. venv/bin/activate
pip install Django django-mptt Pillow

cat <<EOD
Everything should be ready now. Type the following commands into the shell
to start the test server:

python manage.py runserver

Navigate to http://127.0.0.1:8000/admin/ to see the admin interface. The
username is 'admin', the password 'password'. You are probably most
interested in the page module.
EOD
