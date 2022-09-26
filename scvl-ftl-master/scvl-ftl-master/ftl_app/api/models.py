from django.db import models
from django.contrib.auth import models as auth_models


# Create your models here.
class SlpId(models.Model):
    user = models.ForeignKey(auth_models.User, on_delete=models.DO_NOTHING, null=False, blank=False, editable=False)
    slp_id = models.CharField(max_length=100, null=False, blank=False, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    active = models.BooleanField(default=True, null=False, blank=False)
    public_key = models.CharField(max_length=44, null=False, blank=False, editable=False)
    private_key = models.CharField(max_length=44, null=False, blank=False, editable=False)
    received_public_key = models.CharField(max_length=44, null=False, blank=False, editable=False)
    received_private_key = models.CharField(max_length=44, null=False, blank=False, editable=False)

    class Meta:
        app_label = "api"
        unique_together = ('user', 'slp_id')


class AddressBook(models.Model):
    user = models.ForeignKey(auth_models.User, on_delete=models.DO_NOTHING, null=False, blank=False)
    alias = models.CharField(max_length=100, null=False, blank=False)
    public_key = models.CharField(max_length=44, null=False, blank=False)

    class Meta:
        app_label = "api"
        unique_together = ('user', 'alias')


class Publication(models.Model):
    slp_id = models.ForeignKey(SlpId, on_delete=models.DO_NOTHING, null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=False, blank=False, unique=True)
    ledger_asset = models.CharField(max_length=100, null=False, blank=False, editable=False, default=None)
    recipient = models.CharField(max_length=44, null=False, blank=False, editable=False, default=None)
    tx_type = models.CharField(max_length=8, null=False, blank=False, editable=False, default=None)

    class Meta:
        app_label = "api"


class Setting(models.Model):
    user = models.ForeignKey(auth_models.User, on_delete=models.DO_NOTHING, null=False, blank=False, editable=False)
    setting = models.CharField(max_length=100, null=False, blank=False, default=None, unique=True)
    value = models.CharField(max_length=100, null=False, blank=False, default=None)

    class Meta:
        app_label = "api"
