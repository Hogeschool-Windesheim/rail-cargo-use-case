from rest_framework import serializers
# from rest_framework_recursive.fields import RecursiveField # Was used in Verifiability, might be useful.
from django.contrib.auth.models import User
import os

from api.models import Setting, SlpId, AddressBook
from api.slp_interface import SlpInterface

from api.status.event_milestones import EventMilestones


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff', 'is_active', 'last_login',)
        # fields = '__all__'
        write_only_fields = ('password',)
        read_only_fields = ('date_joined', 'last_login')

    def create(self, validated_data):
        u = User(username=validated_data['username'])

        u.first_name = validated_data.get('first_name', "")
        u.last_name = validated_data.get('last_name', "")
        u.email = validated_data.get('email', "")
        u.is_staff = validated_data.get('is_staff', False)
        u.is_superuser = validated_data.get('is_superuser', False)
        u.is_active = validated_data.get('is_active', True)

        u.set_password(validated_data['password'])
        u.save()
        return u

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.is_staff = validated_data.get('is_staff', instance.is_staff)
        instance.is_superuser = validated_data.get('is_superuser', instance.is_superuser)
        instance.is_active = validated_data.get('is_active', instance.is_active)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.save()
        return instance


class AddressBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressBook
        fields = ('alias', 'public_key')

    def create(self, validated_data):
        return AddressBook.objects.create(**validated_data)


class SlpIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlpId
        fields = ('active', 'slp_id', 'timestamp', 'public_key')
        read_only_fields = ('slp_id', 'timestamp', 'public_key')

    def create(self, user):
        slp_interface = SlpInterface(
            os.getenv('SLP_URL'),
            os.getenv('SLP_TOKEN')
        )

        try:
            slp_id = slp_interface.create_id(user.username)
        except ValueError as e:
            raise ValueError("Unable to create semantic-ledger ID: %s" % e)

        return SlpId.objects.create(
            user=user,
            slp_id=slp_id['id'],
            active=True,
            public_key=slp_id['keys']['keypair']['public_key'],
            private_key=slp_id['keys']['keypair']['private_key'],
            received_public_key=slp_id['keys']['received']['public_key'],
            received_private_key=slp_id['keys']['received']['private_key']
        )


class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, instance):
        serializer = self.parent.parent.__class__(instance, context=self.context)
        return serializer.data


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ('setting', 'value',)


class RawPublicationSerializer(serializers.Serializer):
    publication = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    format = serializers.CharField(required=True)
    slp_id = serializers.CharField(required=False)


class TransferAssetSerializer(serializers.Serializer):
    asset_id = serializers.CharField(required=True)
    recipient = serializers.CharField(required=True)
    slp_id = serializers.CharField(required=False)


# Helper for OrderSerializer
class CargoSerializer(serializers.Serializer):
    # Cargo type: Currently supports "{g|G}eneral"
    cargo_type = serializers.CharField(required=True)
    # Package type: Currently supports "{pallets}"
    package_type = serializers.CharField(required=True)
    package_count = serializers.IntegerField(min_value=1)

"""
OrderInputSerializer parses the Order data object.
It does the brunt of the serialization work, but it is technically
a helper for the OrderCallSerializer, which is the serializer
that gets instantiated in the view code.
"""
class OrderInputSerializer(serializers.Serializer):
    cargo = CargoSerializer(required=True)
    reference_id = serializers.CharField(required=False)
    time_of_acceptance = serializers.DateTimeField(required=True)
    place_of_acceptance = serializers.CharField(required=True)
    time_of_delivery = serializers.DateTimeField(required=True)
    place_of_delivery = serializers.CharField(required=True)

class OrderCallSerializer(serializers.Serializer):
    service_provider = serializers.CharField(required=True)
    order = OrderInputSerializer(required=True)

class EventInputSerializer(serializers.Serializer):
    time = serializers.DateTimeField(required=True)
    place = serializers.CharField(required=True)
    milestone = serializers.IntegerField(required=True)
    # TODO delimit milestone options
            # choices=EventMilestones.known_milestones)

class EventCallSerializer(serializers.Serializer):
    order_asset_id = serializers.CharField(required=True)
    event = EventInputSerializer(required=True)
    # TODO optionally, check length of asset id (64 characters)
    #   probably can even subclass CharField as AssetField etc.
