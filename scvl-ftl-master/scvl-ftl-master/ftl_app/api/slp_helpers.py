"""
A module containing utility functions for interaction with an SLP node.
Actual communication is performed in slp_interface.py.
The present module captures common or intuitive usage patterns of the SLP interface.
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status as http_status

from api.slp_interface import SlpInterface

from api.models import SlpId
import api.semantics as semantics

import os

# Simple wrapper functions
def get_asset(*args, **kwargs):
    return SlpInterface().get_publication(*args, **kwargs)

def transfer(*args, **kwargs):
    return SlpInterface().transfer(*args, **kwargs)

def update(asset_id, slp_id, metadata, recipient_id=None):
    """Add a transaction with new data to an asset's history.

    Unless a recipient is indicated, the asset ownership
    structure should be left unchanged."""
    # Default to transfer-to-self
    # TODO The method could support multi-sig ownership,
    # Checking the current unspent outputs and replicating them
    # so the same conditions apply post-transfer.
    if not recipient_id:
        recipient_id = slp_id
    # Perform transfer call
    tx_id = transfer(
        asset_id=asset_id,
        slp_id=slp_id.slp_id,
        private_key=slp_id.private_key,
        recipient=recipient_id.public_key,
        metadata=metadata
    )
    # Return the ID of the new transfer transaction
    return tx_id


def all_assets(user, type=None, history=False, created=False):
    """
    Return all assets owned by a user.

    @type: an optional way of filtering for assets of a particular type.
    @history: if True, returns all assets the user had some involvement in
    (i.e. was at some point owner of).
    @created: if True, returns only assets the user was a creator of

    The return object is a dictionary where the keys are asset IDs and the values
    are dictionaries containing all the asset data.
    """
    slp_interface = SlpInterface()

    # Retrieve user's SLP IDs
    try:
        slp_ids = SlpId.objects.filter(user=user, active=True)
        # Extract the actual SLP-ID string from the complex SLP-ID object
        slp_ids = [id.slp_id for id in slp_ids]
    except ObjectDoesNotExist:
        # TODO any special exception handling?
        raise ObjectDoesNotExist("Could not retrieve user's SLP IDs")

    # collect assets
    assets = {}
    for slp_id in slp_ids:
        try:
            if history:
                # Get all transactions in a user's history, grouped by asset
                assetDicts = slp_interface.get_history_of_user(slp_id, created=created)
            else:
                # Send asData=True flag, else this only returns asset IDs!
                assetDicts = slp_interface.get_assets_of(slp_id, asData=True)
        except Exception as e:
            #TODO handle exception type?
            raise e
        
        # Extract only the assets
        for assetID, assetDict in assetDicts.items():
            asset = assetDict['asset']
            if 'id' not in asset:
                # CREATE transactions do not insert an 'id' field...
                # TODO fix this in the SLP platform
                asset['id'] = assetID
            assets[assetID] = asset
    
    if type:
        assets = {assetID:asset for (assetID, asset) in assets.items()
                    if semantics.has_type(type, asset)}
    
    return assets

def owns(user, asset_id):
    """
    Determine if an asset exists and
    whether it is owned by a given user.
    """

    # Create interface to SLP
    slp_interface = SlpInterface(
        os.getenv('SLP_URL'),
        os.getenv('SLP_TOKEN')
    )

    # Retrieve asset
    try:
        asset = slp_interface.get_publication(asset_id)
    except ValueError:
        # The asset does not exist
        return False
    
    # Retrieve user's SLP IDs
    try:
        slp_ids = SlpId.objects.filter(user=user, active=True)
        # Extract the actual SLP-ID string from the complex SLP-ID object
        slp_ids = [id.slp_id for id in slp_ids]
    except ObjectDoesNotExist:
        # TODO any special exception handling?
        return False
    
    # For each SLP ID, check if the asset is among the
    # assets owned by that ID
    for slp_id in slp_ids:
        try:
            user_assets = slp_interface.get_assets_of(slp_id)
        except Exception as e:
            # TODO handle some exceptions differently? E.g. bad request could be passed on.. 
            print('Cannot check asset ownership:', str(e))
            continue
        for user_asset in user_assets:
            if asset_id == user_asset['asset_id']:
                return True

    # If no to the above, the user does not own the asset
    return False


def previousOwner(asset_id):
    """
    For a given asset, retrieve its owner before it was
    last transferred.
    """

    # Create interface to SLP
    slp_interface = SlpInterface(
        os.getenv('SLP_URL'),
        os.getenv('SLP_TOKEN')
    )

    # TODO BUG if this is called with asset ID it can only check the owner making the original transaction;
    # subsequent transfers are not registered, as the tx_id is different from the asset_id.
    asset_inputs = slp_interface.get_inputs(asset_id)

    # Verify inputs
    if not len(asset_inputs) == 1:
        return Response('Asset has multiple inputs',
                        status=http_status.HTTP_400_BAD_REQUEST)

    if not len(asset_inputs[0]['owners_before']) == 1:
        return Response('Asset is multisig asset',
                        status=http_status.HTTP_400_BAD_REQUEST)

    prev_owner = asset_inputs[0]['owners_before'][0]
    return prev_owner

def get_transactions(asset_id, type=None, **kwargs):
    """
    Retrieve all transactions for an asset.

    Use :type to filter by semantic type.
    """
    # TODO Type filtering can probably also happen in slp_interface,
    # or even in the slp platform.
    # TODO It seems clunky to have to juggle different txs in specific functions;
    # couldn't we create abstract TX objects whenever we get them, so we
    # don't have to worry about this?
    txs = SlpInterface().get_transactions(asset_id, kwargs)
    if type:
        filtered_txs = []
        for tx in txs:
            # Set up the path to get the data from the tx object
            data_key = lambda tx_dict: tx_dict['metadata']['data']
            if tx['operation'] == "CREATE":
                # Data is stored in a different place for CREATE transactions
                data_key = lambda tx_dict: tx_dict['asset']['data']
            # Do the typechecking
            try:
                if semantics.has_type(type, data_key(tx)):
                    filtered_txs.append(tx)
            except KeyError:
                # Tx does not contain data
                continue
        # Continue working with the filtered txs only
        txs = filtered_txs
    return txs
