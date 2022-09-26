from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from rest_framework.authtoken.models import Token

from api.serializers import SlpIdSerializer


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_slp_id(sender, instance=None, created=False, **kwargs):
    if created:
        serializer = SlpIdSerializer(data={'active': True})
        if not serializer.is_valid():
            raise ValueError("Unable to create semantic-ledger ID")
        serializer.create(instance)
