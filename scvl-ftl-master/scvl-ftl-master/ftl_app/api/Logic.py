"""
A module that defines and handles logic checks that are commonly used.
Methods here will typically be called from views.
"""

import api.slp_helpers as slp_helpers
import api.semantics as semantics

from rest_framework.response import Response
from rest_framework import status as http_status

from api.status.status import Status

def checkLogic(listOfChecks):
    """
    Given a list of conditions and relevant arguments,
    this module runs through all conditions and checks whether
    the logic is satisfied.

    If a logic check fails, the method returns a Response, 
    (typically with an error message),
    that can be used by a view.
    Hence, the return variable is called @response.

    If all checks pass, the view does not need to send a Response
    so the method will return None.
    """
    for condition, args in listOfChecks:
        response = condition(*args)
        if response:
            # Immediately return the response, since we
            # only send one response anyway.
            return response
    
    return None

# TODO for all exceptions below, catch various exception types for different responses...

# NOTE: All methods return None by default. 
# https://stackoverflow.com/questions/15300550/return-return-none-and-no-return-at-all#15300671

def asset_exists(asset_id):
    """
    Given an asset ID, confirm that the asset exists on the ledger.
    """
    try:
        slp_helpers.get_asset(asset_id)
    except Exception as e:
        return Response(str(e), status=http_status.HTTP_400_BAD_REQUEST)


def asset_has_type(asset_id, semantic_type):
    """
    Given an asset ID and a semantic type, confirm
    that the asset's rdf contains a subject of the given type.
    """
    try:
        asset = slp_helpers.get_asset(asset_id)
        if not semantics.has_type(semantic_type, asset):
            return Response('Asset is not of type {}'.format(str(semantic_type)), status=http_status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(str(e), status=http_status.HTTP_400_BAD_REQUEST)

def asset_owned_by(asset_id, user):
    """
    Given an asset ID and a user account,
    confirm that the user owns this asset on the ledger.
    """
    if not slp_helpers.owns(user, asset_id):
        return Response('User does not own asset', status=http_status.HTTP_400_BAD_REQUEST)

def asset_status_equals(asset_id, target_status, status_class):
    """
    Check that an asset has a target status.
    """
    try:
        actual_status = status_class.get_status(asset_id)
    except Exception as e:
        return Response('Cannot ascertain asset status',
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not actual_status == target_status:
        return Response('Incorrect asset status: {} should have been {}'.format(actual_status, target_status),
            status=http_status.HTTP_400_BAD_REQUEST)

def asset_status_not_equals(asset_id, avoid_statuses, status_class):
    """
    Check that an asset does not have one of a list of statuses.

    Also accepts a singleton value for avoid_statuses.
    """
    # TODO refactor status_equals
    # to accept lists,
    # then call status_equals and NOT the result?
    # TODO update for Status refactor;
    # get status in the context of a status class
    try:
        actual_status = status_class.get_status(asset_id)
    except Exception as e:
        return Response('Cannot ascertain asset status: {}'.format(str(e)),
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # badStatus tracks whether the asset's status is undesirable
    bad_status = False
    try:
        for avoid_status in avoid_statuses:
            if actual_status == avoid_status:
                # Status is undesirable
                bad_status = True
                break
    except TypeError:
        # avoidStatuses is a singleton, not a list
        bad_status = (actual_status == avoid_statuses)
    
    if bad_status:
        return Response('Unacceptable asset status ({})'.format(actual_status),
            status=http_status.HTTP_400_BAD_REQUEST)


# def assetStatusNot(assetID, avoidStatuses):
#     """
#     Given an asset id (that is presumed to be an Order)
#     and a collection of statuses-to-be-avoided @avoidStatuses,
#     this function checks that the order status is
#     NOT of a value among the statuses to be avoided.

#     """
#     try:
#         assetStatus = OrderStatus.getOrderStatus(assetID)
#     except Exception as e:
#         return Response('Cannot ascertain asset status',
#             status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     # badStatus tracks whether the asset's status is undesirable
#     badStatus = False
#     try:
#         for status in avoidStatuses:
#             if assetStatus == status:
#                 # Status is undesirable
#                 badStatus = True
#                 break
#     except TypeError:
#         # avoidStatuses is a singleton, not a list
#         badStatus = assetStatus == avoidStatuses
    
#     if badStatus:
#         return Response('Unacceptable asset status ({})'.format(assetStatus),
#             status=http_status.HTTP_400_BAD_REQUEST)
