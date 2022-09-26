from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import status as http_status

import api.Logic as Logic
from api.status.order_status import OrderStatus
from api.models import AddressBook, Setting, SlpId
from api.openapi import OrderSchema
from api.semantics import Semantics
from api.serializers import RawPublicationSerializer, OrderCallSerializer
import api.slp_helpers as slp_helpers
from api.slp_interface import SlpInterface

import os

# Views
class OrderView(APIView):
    """
    Create an order or list a user's orders.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    schema = OrderSchema()

    def get(self, request):
        """
        Retrieves all orders that a user has participated in.
        Since users can interact with orders in two ways,
        this endpoint allows for a query argument to restrict
        the request to a certain role.

        ?role={customer|provider} List only orders where user played @role
        ?completed={true|false} List only orders that are/are not completed

        The return data is a dictionary structured by asset ID.
        Each member contains the asset and the order status.
        For example:
        {<asset_id_1>: {}
            'asset': <asset:string>,
            'status':<status:int>
            },
         <asset_id_2>: ...
        }
        """

        # Retrieve query arguments
        # TODO how to sanitize? Should this be serialized?
        role = request.GET.get('role', '')
        completed = request.GET.get('completed', '')

        # TODO handle users calling this endpoint without authentication
        # (they should probably be blocked and receive a neat Response)

        try:
            # Crucially, set history to True
            orders = slp_helpers.all_assets(request.user, type=Semantics().SCVL.Order, history=True)
        except Exception as e:
            return Response('Could not retrieve orders:' + str(e), status=http_status.HTTP_400_BAD_REQUEST)

        # For each order asset, determine its current metadata
        orderdict = {}
        for asset_id, asset_dict in orders.items():
            status = OrderStatus.get_status(asset_id)
            asset_dict["metadata"] = {
                "status":status,
                "roles":{
                    "customer":"Undefined",
                    "service-provider":"Undefined"
                }
            }
            orderdict[asset_id] = asset_dict

        return Response(orderdict, status=http_status.HTTP_200_OK)

    def post(self, request):
        # Serialize and validata the input data
        serializer = OrderCallSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response("Invalid input: {}".format(e), status=http_status.HTTP_400_BAD_REQUEST)

        # Determine SLP ID to use for posting
        if 'slp_id' in serializer.validated_data:
            try:
                slp_id = SlpId.objects.get(user=request.user, active=True, slp_id=serializer.validated_data["slp_id"])
            except SlpId.DoesNotExist:
                return Response("Provided SLP ID does not exist or is not active", status=http_status.HTTP_404_NOT_FOUND)
        else:
            try:
                # get most recent, active, slp-id
                slp_id = SlpId.objects.filter(user=request.user, active=True).order_by('-timestamp')[0]
            except SlpId.DoesNotExist:
                return Response("SLP ID does not exist", status=http_status.HTTP_404_NOT_FOUND)

        order_rdf = Semantics().create_order(serializer.validated_data['order'], returns='string')

        try:
            recipient = AddressBook.objects.get(
                user=request.user,
                alias=serializer.validated_data['service_provider']
            ).public_key
        except AddressBook.DoesNotExist:
            return Response('Unknown recipient', status=http_status.HTTP_404_NOT_FOUND)

        try:
            publication_shape_asset = Setting.objects.get(setting='order_shape')
        except ObjectDoesNotExist:
            return Response("order_shape setting not set", status=http_status.HTTP_404_NOT_FOUND)

        # Create interface to SLP
        slp_interface = SlpInterface(
            os.getenv('SLP_URL'),
            os.getenv('SLP_TOKEN')
        )

        # Post the order rdf to the ledger
        try:
            ledger_asset = slp_interface.publish(
                slp_id=slp_id.slp_id,
                private_key=slp_id.private_key,
                payload=order_rdf,
                shape=publication_shape_asset.value,
                recipient=recipient,
            )
        except ValueError as e:
            return Response("Could not publish: %s" % e, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(ledger_asset, status=http_status.HTTP_200_OK)


class OrderDetailView(APIView):
    """
    Confirm or reject an order, or view the details of a specific order.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    # Even viewing orders should have restrictions on permission, so we use IsAuthenticated (not OrReadOnly)
    permission_classes = (IsAuthenticated,)

    schema = OrderSchema()

    def get(self, request, asset_id):
        """
        Retrieve the details of a single order.
        Also retrieve all events that were posted in
        relation to the order.
        """
        # Check logic and return any response if the check fails
        logic_response = Logic.checkLogic([
            (Logic.asset_exists, [asset_id]),
            (Logic.asset_has_type, [asset_id, Semantics().SCVL.Order]),
            # (Logic.asset_owned_by, [asset_id, request.user])
        ])
        if logic_response: return logic_response

        try:
            # Retrieve order asset
            order = slp_helpers.get_asset(asset_id)
            # Retrieve all events of user
            event_txs = slp_helpers.get_transactions(asset_id, type=Semantics.SCVL.Event, sort=True)
            # Trim to only the event data
            event_data = []
            for event_tx in event_txs:
                try:
                    event = event_tx['metadata']['data']
                    event_data.append(event)
                except (KeyError, TypeError) as e:
                    print("Warning: Cannot access event data from tx: {}".format(e))
            # Get order status
            status = OrderStatus.get_status(asset_id)
        except Exception as e:
            return Response("Error while retrieving assets: {}".format(e),
                            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Build return object
        responseDict = {
            'order':order,
            'events':event_data,
            'metadata':{
                'status': status,
                'roles':{
                    'customer':"Undefined",
                    'service-provider':"Undefined"
                }
            }
        }
        return Response(data=responseDict,
                        status=http_status.HTTP_200_OK)


    def put(self, request, asset_id):
        """
        After an order has been placed, this PUT call
        will send out an order confirmation.
        """
        
        # Check logic and return any response if the check fails
        logic_response = Logic.checkLogic([
            (Logic.asset_exists, [asset_id]),
            (Logic.asset_has_type, [asset_id, Semantics().SCVL.Order]),
            (Logic.asset_owned_by, [asset_id, request.user])
        ])
        if logic_response: return logic_response

        # Post a vacuous TRANSFER that keeps the asset in the user's property.
        # This allows the ledger to register an update,
        # and include metadata indicating the 'CONFIRM' status change.
        try:
            user_slp_id = SlpId.objects.filter(user=request.user, active=True).order_by('-timestamp')[0]
            slp_helpers.transfer(
                asset_id=asset_id,
                slp_id=user_slp_id.slp_id,
                private_key=user_slp_id.private_key,
                recipient=user_slp_id.public_key,
                metadata={
                    'metadata':{'status':OrderStatus.CONFIRMED}
                }
            )            
        except Exception as e:
            return Response(str(e), status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response('Order confirmed for asset ID {}'.format(asset_id), status=http_status.HTTP_200_OK)

    def delete(self, request, asset_id):
        """
        After an order has been placed, this DELETE call
        will send out an order rejection.
        """

        # Check logic and return any response if the check fails
        logic_response = Logic.checkLogic([
            (Logic.asset_exists, [asset_id]),
            (Logic.asset_has_type, [asset_id, Semantics().SCVL.Order]),
            (Logic.asset_owned_by, [asset_id, request.user]),
            (Logic.asset_status_equals, [asset_id, OrderStatus.TO_BE_CONFIRMED, OrderStatus]),
        ])
        if logic_response: return logic_response
        
        # Transfer the asset back to the original owner.
        try:
            # Set up variables for transfer
            prev_owner = slp_helpers.previousOwner(asset_id)
            user_slp_id = SlpId.objects.filter(user=request.user, active=True).order_by('-timestamp')[0]
            
            slp_helpers.transfer(
                asset_id=asset_id,
                slp_id=user_slp_id.slp_id,
                private_key=user_slp_id.private_key,
                recipient=prev_owner,
                metadata={
                    'metadata':{'status':OrderStatus.REJECTED}
                }
            )
        except Exception as e:
            return Response(str(e), status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response('Order rejected for asset ID {}'.format(asset_id), status=http_status.HTTP_200_OK)
