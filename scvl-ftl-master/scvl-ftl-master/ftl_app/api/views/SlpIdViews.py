from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.http import Http404

from api.models import SlpId
from api.serializers import SlpIdSerializer
from api.openapi import SlpIdSchema


class SlpIdList(APIView):
    """
    List all slp-ids, or create a new slp-id
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    schema = SlpIdSchema()

    def get(self, request, format=None):
        slp_ids = SlpId.objects.filter(user=request.user)
        serializer = SlpIdSerializer(slp_ids, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = SlpIdSerializer(data=request.data)
        if serializer.is_valid():
            slp_id = serializer.create(request.user)
            return Response(slp_id.slp_id, status=http_status.HTTP_200_OK)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class SlpIdDetail(APIView):
    """
    Retrieve or delete an SLP-id
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    schema = SlpIdSchema()

    def get_object(self, user, alias):
        try:
            return SlpId.objects.get(user=user, slp_id=alias)
        except SlpId.DoesNotExist:
            raise Http404

    def get(self, request, alias):
        _id = self.get_object(request.user, alias)
        serializer = SlpIdSerializer(_id)
        return Response(serializer.data)

    def delete(self, request, alias):
        _id = self.get_object(request.user, alias)
        try:
            _id.delete()
        except:
            return Response("Could not delete ID", status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response("Deleted %s" % _id.slp_id)

    def put(self, request, alias):
        setting = self.get_object(request.user, alias)
        serializer = SlpIdSerializer(setting, data=request.data)
        if not serializer.is_valid():
            return Response("Invalid request", status=http_status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response("Updated %s" % setting.slp_id, status=http_status.HTTP_200_OK)
