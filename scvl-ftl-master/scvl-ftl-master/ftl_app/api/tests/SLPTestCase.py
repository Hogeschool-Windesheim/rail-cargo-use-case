from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status as http_status

from django.urls import reverse
from django.contrib.auth.models import User

from django.core.management import call_command

import api.tests.testdata as testdata

class SLPTestCase(APITestCase):
    """
    Abstract class that sets up the client,
    as well as some user accounts,
    as well as some helper functions,
    all for the purpose of defining other
    concrete test classes.
    """
    # TODO strip this of FTL-specific cases.
    #   There should be an OrderTestCase that
    #   implement stuff like postOrder.
    #   These can also be separate files,
    #   or even a subfolder that collects all classes.

    client = APIClient()

    @classmethod
    def setUpClass(cls):
        """
        Before running any tests, this method sets up
        the admin account.
        It also posts SHACL shapes and sets the Settings for them.
        """
        # Call super for Django TestCase initialization
        super().setUpClass()

        # Create client
        cls.client = APIClient()

        # Create admin account
        admin = User.objects.create_superuser('admin', '', 'hallo123')

        # Get admin token
        admin_token = Token.objects.get(user__username='admin')

        # Authenticate as admin
        cls.client.credentials(HTTP_AUTHORIZATION='Token ' + admin_token.key)
        
        # get SLP ID from Admin:
        url = reverse('slp_list')
        response = cls.client.get(url)
        # Check that the request was properly processed
        if response.status_code != http_status.HTTP_200_OK:
            print('Error retrieving SLP-IDs:', response.data)
            raise Exception
        admin_slp_id = response.data[0]['slp_id']

        # Set-up SHACL shapes and store as Settings
        # This routes to the manage.py command 'set_shacl'
        call_command('set_shacl', admin_username='admin')

    def setUp(self):
        # TODO docstring

        # Create admin
        admin_token = Token.objects.get(user__username='admin')

        # Create new users
        users = {
            'alice': {
                'slp_id': '',
                'slp_ids': [],
                'token': '',
            },
            'bob': {
                'slp_id': '',
                'slp_ids': [],
                'token': '',
            },
        }

        for username, user in users.items():
            # As admin
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + admin_token.key)

            # API call: create user
            url = reverse('user_view')
            postdata = {
                'username': username,
                'password': 'hallo' + username,
                'is_active': True
            }
            response = self.client.post(url, data=postdata)
            if response.status_code != http_status.HTTP_200_OK:
                print(response.data)
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            print('Created user ' + username)

            # Get user token
            user['token'] = Token.objects.get(user__username=username)
            print(username + " token: {}".format(user['token']))

            # Get user's semantic-ledger ID.
            # First, authenticate as user on the LTVD app
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + user['token'].key)
            
            # Get Semantic-ledger ID's from alice
            url = reverse('slp_list')
            response = self.client.get(url)
            if response.status_code != http_status.HTTP_200_OK:
                print(response.data)
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            user['slp_ids'] = response.data

            # Get specific (first) Semantic-ledger ID
            url = reverse('slp_detail', args=[user['slp_ids'][0]['slp_id']])
            response = self.client.get(url)
            self.assertEqual(response.status_code, http_status.HTTP_200_OK)
            user['slp_id'] = response.data
            print(username + ' uses SLP-ID {}'.format(user['slp_id']))

        # Second loop for users, runs after all users have SLP IDs!!
        # Save users in each other's address books
        for name_a, user_a in users.items():
            # Authenticate
            self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_a['token'].key)

            for name_b, user_b in users.items():
                # Skip self
                if user_a is user_b:
                    continue
                
                # Add user_b to the address book of user_a
                url = reverse('address_list')
                postdata = {
                    'alias': name_b,
                    'public_key': user_b['slp_id']['public_key']
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

    # Helper functions
    @classmethod
    def postOrder(cls, username_a='alice', username_b='bob', order_data=None):
        """
        Post an order to the ledger.
        Returns the asset ID of the post if successful.
        """

        # Set up user variables
        alice = User.objects.get(username=username_a)
        alice_token = Token.objects.get(user=alice).key
        bob = User.objects.get(username=username_b)
        if not order_data:
            order_data = testdata.orders['valid'][0]

        # Authenticate as Alice
        cls.client.credentials(HTTP_AUTHORIZATION='Token ' + alice_token)

        # Post an order
        url = reverse('order')
        postdata = {
            'order': order_data,
            'service_provider': username_b
        }
        response = cls.client.post(url, data=postdata, format='json')

        # Check that the request was properly processed
        if response.status_code != http_status.HTTP_200_OK:
            print('Error while posting order:', response.data)
            raise Exception

        # Extract and return the order asset ID
        order_asset_id = response.data
        return order_asset_id

    @classmethod
    def confirmOrder(cls, order_asset_id, customer_name="alice", service_provider_name="bob"):
        """
        Confirm an order sent from Alice to Bob
        """
        service_provider = User.objects.get(username=service_provider_name)
        sp_token = Token.objects.get(user=service_provider).key

        # Authorize as service provider
        cls.client.credentials(HTTP_AUTHORIZATION="Token {}".format(sp_token))

        # Call the confirm endpoint
        url = reverse('order_detail', kwargs={"asset_id":order_asset_id})
        response = cls.client.put(url)

        if response.status_code != http_status.HTTP_200_OK:
            print('Error while confirming order:', response.data)
            raise RuntimeError

        return response.data