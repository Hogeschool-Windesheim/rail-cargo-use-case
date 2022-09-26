#!/bin/bash

rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
python manage.py slp_createsuperuser
python manage.py set_shacl