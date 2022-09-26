from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.serializers import ValidationError
import os

from api.serializers import TransferAssetSerializer
from api.models import Publication, SlpId, AddressBook
from api.slp_interface import SlpInterface
from api.openapi import TransferSchema

from django.core.exceptions import ObjectDoesNotExist


class MyAssets(APIView):
    """
    Overview of personal assets
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        slp_interface = SlpInterface(
            os.getenv('SLP_URL'),
            os.getenv('SLP_TOKEN')
        )

        try:
            slp_ids = SlpId.objects.filter(user=request.user, active=True).order_by('-timestamp')
        except ObjectDoesNotExist:
            return Response("User ID does not exist", status=http_status.HTTP_404_NOT_FOUND)

        all_assets = {}

        for slp_id in slp_ids:
            try:
                assets = slp_interface.get_assets_of(slp_id.slp_id)
            except ValueError as e:
                return Response("Unable to retrieve assets:"+ str(e), status=http_status.HTTP_404_NOT_FOUND)
            all_assets[slp_id.public_key] = assets

        return Response(all_assets, status=http_status.HTTP_200_OK)


class TransferAsset(APIView):
    """
    Transfer asset to other person
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    schema = TransferSchema()

    def post(self, request):
        serializer = TransferAssetSerializer(data=request.data)
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

        # get recipient object
        try:
            recipient = AddressBook.objects.get(user=request.user, alias=serializer.validated_data['recipient'])
        except ObjectDoesNotExist:
            return Response("Recipient unknown", status=http_status.HTTP_404_NOT_FOUND)

        slp_interface = SlpInterface(
            os.getenv('SLP_URL'),
            os.getenv('SLP_TOKEN')
        )

        try:
            transfer = slp_interface.transfer(
                asset_id=serializer.validated_data['asset_id'],
                slp_id=slp_id.slp_id,
                private_key=slp_id.private_key,
                recipient=recipient.public_key
            )
        except ValueError as e:
            return Response("Could not transfer: %s" % e, status=http_status.HTTP_400_BAD_REQUEST)

        publication = Publication(
            slp_id=slp_id,
            description="{}.{}.{}".format(serializer.validated_data['asset_id'], slp_id.public_key, recipient.public_key),
            ledger_asset=serializer.validated_data['asset_id'],
            recipient=recipient,
            tx_type="TRANSFER"
        )

        publication.save()

        return Response(transfer, status=http_status.HTTP_200_OK)
