from rest_framework.schemas import AutoSchema, ManualSchema
from rest_framework.compat import coreapi, coreschema


class TransferSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'POST':
            extra_fields = [
                coreapi.Field(
                    name="asset_id",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Asset ID",
                        description="Asset ID to transfer"
                    )
                ),
                coreapi.Field(
                    name="recipient",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Recipient",
                        description="Recipient (address) of asset"
                    )
                ),
                coreapi.Field(
                    name="slp_id",
                    required=False,
                    location="form",
                    schema=coreschema.String(
                        title="SLP ID",
                        description="Ledger ID to transact with"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class PublicationSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'POST':
            extra_fields = [
                coreapi.Field(
                    name="publication",
                    required=True,
                    location="form",
                    schema=coreschema.Object(
                        title="Publication",
                        description="Publication data"
                    )
                ),
                coreapi.Field(
                    name="recipient",
                    required=False,
                    location="form",
                    schema=coreschema.String(
                        title="Recipient",
                        description="Recipient (address) of publication"
                    )
                ),
                coreapi.Field(
                    name="slp_id",
                    required=False,
                    location="form",
                    schema=coreschema.String(
                        title="SLP ID",
                        description="Ledger ID to publish with"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class RawPublicationSchema(ManualSchema):
    def __init__(self):
        fields = [
            coreapi.Field(
                name="publication",
                required=True,
                location="form",
                schema=coreschema.String(
                    title="Publication",
                    description="Publication data (raw semantic form)"
                )
            ),
            coreapi.Field(
                name="format",
                required=True,
                location="form",
                schema=coreschema.String(
                    title="Format",
                    description="Publication format ('json-ld' or 'n3')"
                )
            ),
            coreapi.Field(
                name="description",
                required=True,
                location="form",
                schema=coreschema.String(
                    title="Description",
                    description="Publication description"
                )
            ),
            coreapi.Field(
                name="slp_id",
                required=False,
                location="form",
                schema=coreschema.String(
                    title="SLP ID",
                    description="Ledger ID to publish with"
                )
            )
        ]
        description = "Publish raw data"
        super().__init__(fields, description)


class SlpIdDetailSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'PUT':
            extra_fields = [
                coreapi.Field(
                    name="active",
                    required=True,
                    location="form",
                    schema=coreschema.Boolean(
                        title="Active",
                        description="Make ID active/inactive"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class SettingDetailSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'PUT':
            extra_fields = [
                coreapi.Field(
                    name="value",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Value",
                        description="Setting value"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class SettingListSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'POST':
            extra_fields = [
                coreapi.Field(
                    name="setting",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Setting",
                        description="Setting key"
                    )
                ),
                coreapi.Field(
                    name="value",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Value",
                        description="Setting value"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class AddressbookListSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'POST':
            extra_fields = [
                coreapi.Field(
                    name="alias",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Alias",
                        description="Alias to store address"
                    )
                ),
                coreapi.Field(
                    name="public_key",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Public key",
                        description="Public key to store"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class AddressbookDetailSchema(AutoSchema):
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'PUT':
            extra_fields = [
                coreapi.Field(
                    name="public_key",
                    required=True,
                    location="form",
                    schema=coreschema.String(
                        title="Public key",
                        description="Public key to store"
                    )
                )
            ]
        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields


class UserListSchema(AutoSchema):
    """
    Overrides `get_manual_fields()` to provide correct schema
    """
    def get_manual_fields(self, path, method):
        extra_fields = []
        if method == 'POST' or method == 'PUT':
            if method == 'POST':
                extra_fields = [
                    coreapi.Field(
                        name="username",
                        required=True,
                        location='form',
                        schema=coreschema.String(
                            title="Username",
                            description="Username"
                        )
                    ),
                    coreapi.Field(
                        name="password",
                        required=True,
                        location='form',
                        schema=coreschema.String(
                            title="Password",
                            description="New user password"
                        )
                    )
                ]

            if method == 'PUT':
                extra_fields = [
                    coreapi.Field(
                        name="password",
                        required=False,
                        location='form',
                        schema=coreschema.String(
                            title="Password",
                            description="New user password"
                        )
                    )
                ]

            extra_fields = extra_fields + [
                coreapi.Field(
                    name="is_staff",
                    required=False,
                    location='form',
                    schema=coreschema.Boolean(
                        title="Staff",
                        description="Staff status"
                    )
                ),
                coreapi.Field(
                    name="is_superuser",
                    required=False,
                    location='form',
                    schema=coreschema.Boolean(
                        title="Superuser",
                        description="Superuser status"
                    )
                ),
                coreapi.Field(
                    name="is_active",
                    required=False,
                    location='form',
                    schema=coreschema.Boolean(
                        title="Active",
                        description="Active status"
                    )
                ),
                coreapi.Field(
                    name="first_name",
                    required=False,
                    location='form',
                    schema=coreschema.String(
                        title="First name",
                        description="First name"
                    )
                ),
                coreapi.Field(
                    name="last_name",
                    required=False,
                    location='form',
                    schema=coreschema.String(
                        title="Last name",
                        description="Last name"
                    )
                ),
                coreapi.Field(
                    name="email",
                    required=False,
                    location='form',
                    schema=coreschema.String(
                        title="E-mail",
                        description="E-mail address"
                    )
                ),
            ]

        manual_fields = super().get_manual_fields(path, method)
        return manual_fields + extra_fields