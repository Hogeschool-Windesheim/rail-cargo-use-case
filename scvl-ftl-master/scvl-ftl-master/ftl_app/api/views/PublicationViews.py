from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.serializers import ValidationError
from django.core.exceptions import ObjectDoesNotExist
import os

from api.serializers import RawPublicationSerializer
from api.models import Publication, SlpId, Setting, AddressBook
from api.slp_interface import SlpInterface
from api.semantics import Semantics
from api.openapi import RawPublicationSchema


class RawPublicationsView(APIView):
    """
    Create new or retrieve verifiable publications
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)

    schema = RawPublicationSchema()

    def post(self, request):
        serializer = RawPublicationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response("Invalid input", status=http_status.HTTP_400_BAD_REQUEST)

        if 'slp_id' in serializer.validated_data:
            try:
                slp_id = SlpId.objects.get(user=request.user, active=True, slp_id=serializer.validated_data["slp_id"])
            except ObjectDoesNotExist:
                return Response("Provided Ledger-ID does not exist or is not active", status=http_status.HTTP_404_NOT_FOUND)
        else:
            try:
                # get most recent, active, slp-id
                slp_id = SlpId.objects.filter(user=request.user, active=True).order_by('-timestamp')[0]
            except ObjectDoesNotExist:
                return Response("User ID does not exist", status=http_status.HTTP_404_NOT_FOUND)

        slp_interface = SlpInterface(
            os.getenv('SLP_URL'),
            os.getenv('SLP_TOKEN')
        )

        try:
            ledger_asset = slp_interface.publish(
                slp_id=slp_id.slp_id,
                private_key=slp_id.private_key,
                payload=serializer.validated_data['publication'],
                format=serializer.validated_data['format']
            )
        except ValueError as e:
            return Response("Could not publish: %s" % e, status=http_status.HTTP_400_BAD_REQUEST)

        publication = Publication(
            slp_id=slp_id,
            description=serializer.validated_data['description'],
            ledger_asset=ledger_asset,
            recipient="self",
            tx_type="CREATE"
        )

        publication.save()
        return Response(ledger_asset, status=http_status.HTTP_200_OK)
