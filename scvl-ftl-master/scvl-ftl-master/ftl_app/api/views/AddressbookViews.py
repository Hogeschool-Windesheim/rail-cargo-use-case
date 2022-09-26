from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.http import Http404

from api.models import AddressBook
from api.serializers import AddressBookSerializer
from api.openapi import AddressSchema


class AddressbookList(APIView):
    """
    List all address book entries or create a new entry
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    schema = AddressSchema()

    def get(self, request, format=None):
        addresses = AddressBook.objects.filter(user=request.user)
        serializer = AddressBookSerializer(addresses, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request, format=None):
        serializer = AddressBookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.validated_data, status=http_status.HTTP_200_OK)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class AddressbookDetail(APIView):
    """
    Retrieve, update or delete an addressbook entry
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)

    schema = AddressSchema()

    def get_object(self, user, alias):
        try:
            return AddressBook.objects.get(user=user, alias=alias)
        except AddressBook.DoesNotExist:
            raise Http404

    def get(self, request, alias):
        address_entry = self.get_object(request.user, alias)
        serializer = AddressBookSerializer(address_entry)
        return Response(serializer.data)

    def delete(self, request, alias):
        address_entry = self.get_object(request.user, alias)
        try:
            address_entry.delete()
        except:
            return Response("Could not delete addressbook entry", status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response("Deleted %s" % address_entry.alias)

    def put(self, request, alias):
        address_entry = self.get_object(request.user, alias)
        serializer = AddressBookSerializer(address_entry, data=request.data)
        if not serializer.is_valid():
            return Response("Invalid request: %s" % serializer.error_messages, status=http_status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response("Updated %s" % address_entry.alias, status=http_status.HTTP_200_OK)
