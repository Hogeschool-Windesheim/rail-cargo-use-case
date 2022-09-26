from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework import status as http_status

import api.Logic as Logic
from api.serializers import EventCallSerializer
from api.models import AddressBook, Setting, SlpId
from api.slp_interface import SlpInterface
import api.slp_helpers as slp_helpers
from api.semantics import Semantics
# import api.semantics as semantics
from api.openapi import EventSchema
from api.status.event_milestones import EventMilestones
from api.status.order_status import OrderStatus

import os
import json

def locationLogic(milestone, validated_data, order_asset):
    """
        # Location logic, based on milestones

        The function determines if conditions relating to the milestone are met.
        If this is NOT the case, the method returns an error response.
        In other words, a successful evaluation of milestone logic
        results in returning None.
    """

    # Set switch dictionary
    # Possibly, when the complexity of the application grows,
    # this should be refactored into an object-oriented solution.
    switch = {
        EventMilestones.DISCHARGE: {
            'error_message': "Event place {event_place} does not match order place of delivery",
            'condition': lambda **kwargs: Semantics.triple_exists(order_asset['rdf'],
                (None, kwargs['end_place_prop'], kwargs['event_place']))
        },
        EventMilestones.POSITION: {
            'error_message': "Event place {event_place} should not match place of order acceptance or delivery",
            'condition': lambda **kwargs: not (
                Semantics.triple_exists(order_asset['rdf'],
                    (None, kwargs['start_place_prop'], kwargs['event_place']))
                or Semantics.triple_exists(order_asset['rdf'],
                    (None, kwargs['end_place_prop'], kwargs['event_place']))
            )
        },
        EventMilestones.ARRIVE: {
            'error_message': "Event place {event_place} does not match order place of delivery",
            'condition': lambda **kwargs: Semantics.triple_exists(order_asset['rdf'],
                (None, kwargs['end_place_prop'], kwargs['event_place']))
        },
        EventMilestones.DEPART: {
            'error_message': "Event place {event_place} does not match order place of acceptance",
            'condition': lambda **kwargs: Semantics.triple_exists(order_asset['rdf'],
                (None, kwargs['start_place_prop'], kwargs['event_place']))
        },
        EventMilestones.LOAD: {
            'error_message': "Event place {event_place} does not match order place of acceptance",
            'condition': lambda **kwargs: Semantics.triple_exists(order_asset['rdf'],
                (None, kwargs['start_place_prop'], kwargs['event_place']))
        },
        
    }

    # Set keyword arguments for the switch
    # NOTE RDF literals need to be in quotes,
    # so the data is formatted to be in quotes here.
    switch_kwargs = {
        'event_place': '"{}"'.format(validated_data['event']['place']),
        'start_place_prop': 'scvl:placeOfAcceptance',
        'end_place_prop': 'scvl:placeOfDelivery',
    }

    # Check the relevant condition and
    # return an error message if needed
    #BUG the search terms in the triples need to be encoded semantically.
    # They need to process context and indicate if they are literals or URIRef .
    # SO it can match e.g. (rdflib.term.URIRef('bdb://[id]/'), rdflib.term.URIRef('http://ontology.tno.nl/scvl#placeOfAcceptance'), rdflib.term.Literal('Soesterberg'),
    if not switch[milestone]['condition'](**switch_kwargs):
        return switch[milestone]['error_message'].format(**switch_kwargs) + "\n\n Graph:\n {}".format('\n'.join(map(str, list(Semantics.load_rdf(json.dumps(order_asset['rdf'])).quads()))))

    # If nothing else triggered an error response,
    # simply return without any response.
    return None



class EventView(APIView):
    """
    Views to post or retrieve events.

    Note that events don't have their own retrieval methods, since
    the data objects are relatively simple. Lists of events are
    retrieved in the context of a single order.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticatedOrReadOnly,)

    schema = EventSchema()

    def post(self, request):
        """
        Post an event.
        """
        # Serialize and validata the input data
        serializer = EventCallSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            return Response("Invalid input: {}".format(e), status=http_status.HTTP_400_BAD_REQUEST)
        # Retrieve order
        order_asset_id = serializer.validated_data['order_asset_id']

        # Check basic logic
        logic_response = Logic.checkLogic([
            (Logic.asset_exists, [order_asset_id]),
            (Logic.asset_has_type, [order_asset_id, Semantics().SCVL.Order]),
            # TODO better to phrase positively in case of introducing new status;
            # should indicate list of target statuses, but this needs
            # refactoring in Logic.py.
            # TODO also need to check the correct correspondence between
            # event milestone and order status
            (Logic.asset_status_not_equals, [order_asset_id, [OrderStatus.TO_BE_CONFIRMED, OrderStatus.COMPLETED], OrderStatus]),
        ])
        if logic_response: return logic_response

        # Get variables needed for checking milestone-specific logic
        # Extract milestone from data
        milestone = serializer.validated_data['event']['milestone']
        
        # Get order
        slp_interface = SlpInterface()
        try:
            order_asset = slp_interface.get_publication(order_asset_id)
        except Exception as e:
            return Response("Error posting event: Could not retrieve order details: {}".format(e),
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check milestone-specific location logic
        location_logic_message = locationLogic(milestone, serializer.validated_data, order_asset)
        # Handle failure of milestone logic
        if location_logic_message:
            return Response ('Milestone logic failure: {}'.format(location_logic_message),
                status=http_status.HTTP_400_BAD_REQUEST)

        # Create semantics
        event_rdf = Semantics().create_event(serializer.validated_data, returns='string')
        # Since this will be a transfer, not a create, we already load the data as JSON here
        # (for creates, this is done in the platform)
        # TODO unify this..
        event_rdf = json.loads(event_rdf)
        # Get SHACL shape for the event
        try:
            event_shape_asset = Setting.objects.get(setting='event_shape')
        except ObjectDoesNotExist:
            return Response("event_shape setting not set", status=http_status.HTTP_404_NOT_FOUND)
        # Construct the payload to be sent to the ledger
        payload = {
            "data":{
                "rdf":event_rdf,
                "constraints":event_shape_asset.value
            },
            "metadata":{}
        }

        # Decide if the process status should change,
        # based on the nature of the milestone
        # TODO can we run this by EventMilestones.transitions ?
        new_status = None
        if milestone == EventMilestones.LOAD:
            new_status = OrderStatus.STARTED
        elif milestone == EventMilestones.DISCHARGE:
            new_status = OrderStatus.COMPLETED
        # Add the new status to payload
        if new_status:
            payload["metadata"]["status"] = new_status

        # Determine SLP ID to use for posting
        # TODO can we put this code in viewutils?
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

        # Post the event to the ledger
        # in the form of an update to the
        # existing order asset.
        try:
            event_asset_id = slp_helpers.update(
                asset_id=order_asset_id,
                slp_id=slp_id,
                metadata=payload
            )
        except ValueError as e:
            return Response("Could not publish: %s" % e, status=http_status.HTTP_400_BAD_REQUEST)




        return Response(event_asset_id, status=http_status.HTTP_200_OK)

