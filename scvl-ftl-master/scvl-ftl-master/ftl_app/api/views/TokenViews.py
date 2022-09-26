from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.views import APIView

from django.http import Http404
from django.db import IntegrityError


class CreateTokenViews(APIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (IsAuthenticated,)
    """
    Get, or generate new token
    """
    '''
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="username",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Username",
                        description="Valid username for authentication",
                    ),
                ),
                coreapi.Field(
                    name="password",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )
    '''

    def post(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        try:
            new_token = Token.objects.create(user=user)
        except IntegrityError:
            return Response("Could not create new token", status=http_status.HTTP_400_BAD_REQUEST)
        return Response({'token': new_token.key}, status=http_status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        old_token = Token.objects.get(user=user)
        old_token.delete()

        new_token = Token.objects.create(user=user)

        return Response({'token': new_token.key}, status=http_status.HTTP_200_OK)


class TokenViews(APIView):
    def get(self, request, username, password):
        serializer = AuthTokenSerializer(data={
            'username': username,
            'password': password
        }, context={'request': request})

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        try:
            token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            raise Http404
        return Response({'token': token.key}, status=http_status.HTTP_200_OK)
