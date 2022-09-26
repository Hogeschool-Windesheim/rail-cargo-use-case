import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import DatabaseError


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create SuperUser
        username = os.getenv('USERNAME', 'root')
        password = os.getenv('PASSWORD', 'hallo123')
        u = User(username=username, is_staff=True, is_superuser=True)
        u.set_password(password)

        try:
            u.save()
        except DatabaseError as e:
            raise CommandError("Unable to save superuser: %s" % e)

        self.stdout.write("Superuser '%s' created" % username)
