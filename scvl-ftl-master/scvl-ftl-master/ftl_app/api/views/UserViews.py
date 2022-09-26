from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from django.http import Http404
from django.contrib.auth.models import User

from api.openapi import UserSchema
from api.serializers import UserSerializer


class UserListView(APIView):
    """
    List all, or create a new user
    """

    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)

    schema = UserSchema()

    def get(selfs, requset):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response("Invalid request", status=http_status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(serializer.data, status=http_status.HTTP_200_OK)


class UserDetailView(APIView):
    """
    Get, update or delete single user
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAdminUser,)

    schema = UserSchema()

    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, username):
        user = self.get_user(username)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def delete(self, request, username):
        user = self.get_user(username)
        if user == request.user:
            return Response("You cannot delete yourself", status=http_status.HTTP_400_BAD_REQUEST)
        try:
            user.delete()
        except:
            return Response("Could not delete user", status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(True)

    def put(self, request, username):
        user = self.get_user(username)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response("Invalid request %s" % serializer.error_messages, status=http_status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response("Updated %s" % username, status=http_status.HTTP_200_OK)
