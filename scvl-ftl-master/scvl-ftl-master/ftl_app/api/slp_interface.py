import requests
from datetime import datetime
from rest_framework.status import HTTP_200_OK
import json

import os

class SlpInterface:
    def __init__(self, URL=os.getenv('SLP_URL'), TOKEN=os.getenv('SLP_TOKEN')):
        if not URL or not TOKEN:
            raise AttributeError("URL or TOKEN not set")
        self.slp_url = URL
        self.slp_auth_token = TOKEN

    def create_id(self, username):
        slp_id = "{}_{}".format(username, datetime.now().isoformat())
        r = requests.post(
            "{}/id/".format(self.slp_url),
            data={
                'alias': slp_id
            },
            headers={
                'Authorization': 'Token {}'.format(self.slp_auth_token)
            }
        )

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not save semantic-ledger id(%s): %s" % (r.status_code, r.text))

        return {
            'id': slp_id,
            'keys': r.json()
        }

    def publish(self, slp_id, private_key, payload, format='json-ld', shape=None, recipient=None):

        if not isinstance(payload, str):
            if isinstance(payload, bytes):
                payload = payload.decode()

        data = {
            'crypto_id': slp_id,
            'private_key': private_key,
            'publication': payload,
            'format': format
        }

        if recipient:
            data['recipients'] = [{
                'recipients': (recipient,),
            }]

        if shape:
            shape_param = "bdb://{}/".format(shape)
            data['shapes'] = [{"shape": shape_param, "shape_format": 'json-ld'}]

        url = "{}/publish/".format(self.slp_url)
        r = requests.post(
            url,
            json=data,
            headers={
                "Authorization": "Token {}".format(self.slp_auth_token)
            },
        )

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not save publication to ledger  , %s" % r.text)

        # return transaction ID
        return r.json()

    def transfer(self, asset_id, slp_id, private_key, recipient, metadata=None):
        data = {
            'asset_id': asset_id,
            'crypto_id': slp_id,
            'private_key': private_key,
            'recipients': [{
                'recipients': (recipient,),
                'amount': 1
            }]
        }
        if metadata:
            data['metadata'] = metadata

        url = "{}/transfer/".format(self.slp_url)
        r = requests.post(
            url,
            json=data,
            headers={
                'Authorization': 'Token {}'.format(self.slp_auth_token)
            }
        )

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not transfer asset, %s" % r.text)

        # return transaction ID
        return r.json()

    def validate_publication(self, asset_id):
        url = "{}/validate_asset/{}".format(self.slp_url, asset_id)
        r = requests.get(url)

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not validate asset, %s" % r.text)

        reports = r.json()
        conforms = True
        non_conforming_shapes = []

        for report in reports:
            if not report['conforms']:
                conforms = False
                non_conforming_shapes.append(report['simple'])

        if conforms:
            return True
        else:
            return non_conforming_shapes

    def get_publication(self, asset_id):
        url = "{}/asset/{}".format(self.slp_url, asset_id)
        r = requests.get(url)

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not retrieve asset, %s" % r.text)

        # return transaction ID
        return r.json()

    def get_assets_of(self, slp_id, asData=False):
        url = "{}/assets/{}".format(self.slp_url, slp_id)
        # Add the keyword @asData
        # to get full assets.
        # TODO refactor into two separate function calls...
        if asData:
            url += '/?asData=True'
        r = requests.get(url,
                         headers={'Authorization': 'Token {}'.format(self.slp_auth_token)}
                         )

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not retrieve assets, %s" % r.text)

        # Debug
        # print("Result from get_assets_of: {}".format(r.json()))
        return r.json()

    def get_history_of_user(self, slp_id, created=False):
        """
        Return the full history of a user's activity.

        Returns an overview of all the assets
        that a user has had ownership of at some point.
        Also includes all transactions where the user became owner.

        Setting @created to True will only return assets the user
        created or co-created.

        The format of the return data is a dictionary
        that groups an asset and all its relevant transactions by the asset ID:
        {asset_id1:
            { 'asset': asset,
              'transactions': [tx1, tx2]
            },
         asset_id2:{...}
        }
        """
        url = "{}/history/{}".format(self.slp_url, slp_id)
        params = {}
        if created:
            params['created'] = True
        response = requests.get(url,
                         headers={'Authorization': 'Token {}'.format(self.slp_auth_token)},
                         params=params
                         )

        if response.status_code != HTTP_200_OK:
            #TODO catch specific exceptions?
            raise ValueError("Could not retrieve assets, %s" % response.text)

        # Return the response object
        return response.json()



    def get_inputs(self, tx_id):
        url = "{}/transaction/inputs/{}".format(self.slp_url, tx_id)
        r = requests.get(url)

        if r.status_code != HTTP_200_OK:
            raise ValueError("Could not retrieve inputs of tx %s; %s" % (tx_id, r.text))

        # return transaction ID
        return r.json()

    def get_transactions(self, asset_id, sort=False):
        """
        Retrieve all transactions relating to
        the asset with @asset_id.

        Use @sort=True to receive the transactions
        in chronological order.
        """
        # TODO describe return format
        url = "{}/asset/{}/transactions/".format(self.slp_url, asset_id)
        # Add query arguments
        if sort:
            url += '?sort=True'
        response = requests.get(url)

        if response.status_code != HTTP_200_OK:
            #TODO catch specific exceptions?
            raise ValueError("Could not retrieve transactions: {}".format(response.text))

        # Return the response object
        return response.json()

    def get_block_height(self, tx_id):
        """
        Retrieve the height of the block containing
        the transaction with @tx_id.
        """
        # TODO describe return format
        # TODO set url
        url = "{}/transaction/{}/?block=true".format(self.slp_url, tx_id)
        response = requests.get(url)

        if response.status_code != HTTP_200_OK:
            #TODO catch specific exceptions?
            raise ValueError("Could not determine block height: {}".format(response.text))

        # Return the response object
        # Cast to json to reach the 'block_height' key
        # TODO how to find it without json?
        #   there is no response.data field...
        return response.json()['block_height']