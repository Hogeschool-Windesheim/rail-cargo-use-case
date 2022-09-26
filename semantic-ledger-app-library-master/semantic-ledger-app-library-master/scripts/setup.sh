#!/bin/bash
# Shell script to set up the Django app's database.
# This script should be called from inside the app container,
# because it makes use of the container's environment variables
# and installed python dependencies.
#
# If loading this script from a library, mount it at the app's root folder
# so it has access to db.sqlite3 and manage.py

# Wipe the database
echo "Removing database, if present..."
rm db.sqlite3
# Prepare a new database
python manage.py makemigrations
python manage.py migrate
# Create a root user
python manage.py create_super_user
# Publish shacl shapes and save asset IDs in the database
python manage.py set_shacl
echo "Finished application setup."