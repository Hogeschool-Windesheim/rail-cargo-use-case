import os
from django.db import DatabaseError
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import Setting, SlpId
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime # For time stamping

from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status as http_status




# SHACL Shape file locations
shapes = {
    'order_shape': {
        'relative_filepath':'../../semantics/ftl_order_shape.ttl',
        'asset_id':''
    },
    'event_shape': {
        'relative_filepath':'../../semantics/ftl_event_shape.ttl',
        'asset_id':''
    },
}

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--admin-username',
                            help="The name of the account holding admin permissions")

    def handle(self, *args, **options):
        """
        This command posts all relevant SHACL shapes to the ledger
        and sets the Setting key-value pairs accordingly.

        The command requires the use of a User account with admin permissions.
        @admin_username: A username for a user with admin permissions.
        """
        
        if 'admin_username' in options and options['admin_username']:
            admin_username = options['admin_username']
        else:
            admin_username = 'root'
        
        print('Posting SHACL with username', admin_username)

        # Create client for POST calls
        client = APIClient()

        # Get admin info
        try:
            admin_token = Token.objects.get(user__username=admin_username)
            # get most recent, active, slp-id
            admin_slp_id = SlpId.objects.filter(user__username=admin_username, active=True).order_by('-timestamp')[0].slp_id
        except ObjectDoesNotExist as e:
            raise CommandError("Unable to retrieve admin user info: {}".format(e))


        # Authenticate as admin
        client.credentials(HTTP_AUTHORIZATION='Token ' + admin_token.key)

        # TODO move code below to a helper method?
        for shape_name, shape in shapes.items():
            # Get shape file contents
            shape_path = shape['relative_filepath']
            full_shape_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), shape_path)

            # read shape file
            with open(full_shape_path) as f:
                shape_content = f.read()

            # publish shape
            url = reverse('raw_publication')
            postdata = {
                "publication": shape_content,
                "format": "n3",
                "description": shape_name + str(datetime.now),
                "slp_id": admin_slp_id
            }
            response = client.post(url, data=postdata)

            if response.status_code != http_status.HTTP_200_OK:
                raise CommandError("Failed to publish shape: " + response.data)
            
            shape['asset_id'] = response.data
            print(shape_name, 'asset ID:', shape['asset_id'])

            # Save setting
            # If the setting already exists, update it
            try:
                s = Setting.objects.get(setting=shape_name)
                s.value = shape['asset_id']
                s.save()
            # If the setting does not exist, create it
            except ObjectDoesNotExist:
                s = Setting(user=User.objects.get(username=admin_username), setting=shape_name, value=shape['asset_id'])
                try:
                    s.save()
                except DatabaseError as e:
                    raise CommandError("Unable to save setting: {}".format(e))

        print("All SHACL shapes set")
