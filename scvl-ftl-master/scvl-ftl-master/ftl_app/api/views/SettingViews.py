from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.http import Http404

from api.models import Setting
from api.serializers import SettingSerializer
from api.permissions import IsAdminOrReadOnly
from api.openapi import SettingSchema


class SettingList(APIView):
    """
    List all, or set a setting value
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAdminOrReadOnly,)

    # schema = SettingListSchema()
    schema = SettingSchema()

    def get(self, request):
        settings = Setting.objects.all()
        serializer = SettingSerializer(settings, many=True)
        return Response(serializer.data)

    def post(self, request, **kwargs):
        serializer = SettingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response("Invalid request", status=http_status.HTTP_400_BAD_REQUEST)

        serializer.save(user=request.user)

        return Response(serializer.data, status=http_status.HTTP_200_OK)


class SettingDetail(APIView):
    """
    Retrieve, delete or update specific setting
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    # schema = SettingDetailSchema()
    schema = SettingSchema()

    def get_object(self, setting):
        try:
            return Setting.objects.get(setting=setting)
        except Setting.DoesNotExist:
            raise Http404

    def get(self, request, setting):
        setting = self.get_object(setting)
        serializer = SettingSerializer(setting)
        return Response(serializer.data)

    def delete(self, request, setting):
        setting = self.get_object(setting)
        try:
            setting.delete()
        except:
            return Response("Could not delete setting", status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(True)

    def put(self, request, setting):
        setting = self.get_object(setting)
        serializer = SettingSerializer(setting, data=request.data)
        if not serializer.is_valid():
            return Response("Invalid request", status=http_status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response("Updated %s" % setting, status=http_status.HTTP_200_OK)

