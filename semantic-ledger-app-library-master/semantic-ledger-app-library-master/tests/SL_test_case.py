from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status as http_status

from django.urls import reverse
from django.contrib.auth.models import User

from django.core.management import call_command

from api.models import SlpId

import api.tests.testdata as testdata
import os

class SLTestCase(APITestCase):
    """
    Abstract class that sets up the client,
    admin account,
    user accounts,
    and helper functions,
    all for the purpose of defining other
    concrete test classes.
    """

    client = APIClient()
    adminToken = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store user roles, tokens
        # Subclasses will implement this
        self.roles = []
        self.tokens = {}

    def authorize(self, username):
        """
        Authorize as the user carrying @username.
        """
        # Check for special users
        if username == 'admin':
            authToken = self.adminToken.key
        else:
            authToken = self.tokens[username].key
        # Authorize with token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + authToken)

    def post_object(self, url, data, authorizedUser=None, format="json"):
        """
        Abstract method for posting data objects
        """
        # If desired, authorize as a specific user
        if authorizedUser:
            self.authorize(authorizedUser)
        # Post the object
        response = self.client.post(url, data, format)
        # Check everything went well
        if response.status_code != http_status.HTTP_200_OK:
            raise RuntimeError("Error posting object: "  + response.data)
        return response.data

    def get_object(self, url, authorizedUser=None):
        """Retrieve an asset."""
        # If desired, authorize as a specific user
        if authorizedUser:
            self.authorize(authorizedUser)
        # Get the object
        response = self.client.get(url)
        # Check everything went well
        if response.status_code != http_status.HTTP_200_OK:
            raise RuntimeError("Error retrieving object: "  + response.data)
        return response.data


# Below are standard methods from unittest.
# That is, these methods override those of
# the parent class.
    @classmethod
    def setUpClass(cls):
        """
        Before running any tests, this method sets up
        the admin account.
        It also posts SHACL shapes and sets the Settings for them.
        """
        # Call super for Django TestCase initialization
        super().setUpClass()
        # Create admin account, set admin token
        admin = User.objects.create_superuser('admin', '', 'hallo123')
        cls.adminToken = Token.objects.get(user=admin)
        # Set-up SHACL shapes and store as Settings
        # This routes to the manage.py command 'set_shacl'
        if int(os.getenv("SHACL_ONCHAIN", 0)):
            call_command('set_shacl', admin_username='admin')

    def setUp(self):
        """
        For every test method, create a fresh set of users
        (who do not have any data associated with them yet)
        """

        # Create new users
        users = {role:{
            'slp_id': '',
            'slp_ids': []
        } for role in self.roles}

        # TODO It is questionable whether all these
        # API calls need to be made instead of accessing
        # models directly.
        for username, user in users.items():
            # As admin
            self.authorize('admin')
            # API call: create user
            url = reverse('user_view')
            postdata = {
                'username': username,
                'password': 'hallo' + username,
                'is_active': True
            }
            response = self.client.post(url, data=postdata)
            if response.status_code != http_status.HTTP_200_OK:
                raise RuntimeError(response.data)
            print('Created user ' + username)
            # Get user token
            self.tokens[username] = Token.objects.get(user__username=username)
            print("{} token: {}".format(username, self.tokens[username]))
            # Get user's semantic-ledger ID.
            # First, authorize as user on the LTVD app
            self.authorize(username)            
            # Get Alice's Semantic-ledger ID
            # We order by timestamp to reliably select the same one
            user['slp_id'] = SlpId.objects.filter(user__username=username, active=True).order_by('-timestamp')[0]

        # Second loop for users, runs after all users have SLP IDs!!
        # Save users in each other's address books
        for name_a, user_a in users.items():
            # Authenticate
            self.authorize(name_a)

            for name_b, user_b in users.items():
                # Skip self
                if user_a is user_b:
                    continue
                
                # Add user_b to the address book of user_a
                url = reverse('address_list')
                postdata = {
                    'alias': name_b,
                    'public_key': user_b['slp_id'].public_key
                }
                response = self.client.post(url, data=postdata)
                self.assertEqual(response.status_code, http_status.HTTP_200_OK)
                print("Added {} to {}'s address book".format(name_b, name_a))

                # Get addressbook entries
                response = self.client.get(url)
                self.assertEqual(response.status_code, http_status.HTTP_200_OK)

                # Get 'Alice' addressbook entry
                url = reverse('address_detail', args=[name_b])
                response = self.client.get(url)
                self.assertEqual(response.status_code, http_status.HTTP_200_OK)
                print("Address entry: %s" % response.data)
