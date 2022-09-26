"""
A module to handle requests about the status of a given asset.

#abstract

Author: Jeroen Breteler
Date: 2019-12-27
"""

from api.slp_interface import SlpInterface
import api.slp_util as slp_util

class Status(object):
    """
    Collects a few fields that might be queried in helper functions.
    """

    UNKNOWN = -1
    statuses = [] # Subclasses fill this with known status codes

    @classmethod
    def get_initial_status(cls):
        """
        Return the status of an object that has been created,
        in which case it might not carry any metadata
        that indicates its status.

        The base class implementation assumes that
        cls.statuses is ordered so that the first status
        is the one associated with freshly created assets.
        """
        return cls.statuses[0]


    # Helper methods
    @classmethod
    def get_status(cls, asset_id):
        """
        Determine the current status of an asset.
        @asset_id is the ID of the asset.
        """
        slp_interface = SlpInterface()
        # Get transactions for this asset
        transactions = slp_interface.get_transactions(asset_id, sort=True)
        # Iterate over transactions looking
        # for the latest status update.
        # Order counter-chronologically.
        transactions.reverse()
        for latest_tx in transactions:
            # Determine status
            # If the tx operation is CREATE,
            # the asset is in initial status.
            # (This is also the iteration's terminating case.)
            if latest_tx['operation'] == "CREATE":
                return cls.get_initial_status()
            else:
                # Retrieve the status from the metadata
                try:
                    status = latest_tx['metadata']['metadata']['status']
                    # NOTE: Update-tx'es have "metadata" as a root field
                    # So we select the 'metadata' key twice...
                    if status in cls.statuses:
                        return status
                    # Status code not recognized
                    else:
                        return cls.UNKNOWN
                # Metadata is None or does not contain a status code
                except (KeyError, TypeError):
                    # Keep searching in the next-latest transaction
                    continue

    @classmethod
    def changeStatus(cls, slp_id, asset_id, new_status, recipient_id=None):
        """
        Change the status of an asset.

        Transfer an asset from an slp_id to a recipient,
        indicating the new status in the metadata.
        If the recipient is not indicated, the method defaults
        to transferring the asset to the caller.
        """
        # TODO The method could support multi-sig ownership,
        # Checking the current unspent outputs and replicating them
        # so the same conditions apply post-transfer.
        
        # Default to transfer-to-self
        if not recipient_id:
            recipient_id = slp_id
        # Perform transfer call
        tx_id = slp_util.transfer(
            asset_id=asset_id,
            slp_id=slp_id.slp_id,
            private_key=slp_id.private_key,
            recipient=recipient_id.public_key,
            metadata={'status':new_status}
        )
        # Return the ID of the new transfer transaction
        return tx_id