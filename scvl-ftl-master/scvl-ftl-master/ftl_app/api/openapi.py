from rest_framework.schemas.openapi import AutoSchema


class SettingSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'POST':
            operation['parameters'].append({
                "name": "setting",
                "in": "form",
                "required": True,
                'schema': {
                    'type': 'string',
                },
            })
            operation['parameters'].append({
                "name": "value",
                "in": "form",
                "required": True,
                'schema': {
                    'type': 'string',
                },
            })
        if method == "PUT":
            operation['parameters'].append({
                "name": "value",
                "in": "form",
                "required": True,
                'schema': {
                    'type': 'string',
                },
            })
        return operation


class UserSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'POST' or method == 'PUT':
            if method == 'POST':
                operation['parameters'].append({
                    "name": "username",
                    "in": "form",
                    "required": True,
                    'schema': {
                        'type': 'string',
                    },
                })
                operation['parameters'].append({
                    "name": "password",
                    "in": "form",
                    "required": True,
                    'schema': {
                        'type': 'string',
                    },
                })
            if method == 'PUT':
                operation['parameters'].append({
                    "name": "password",
                    "in": "form",
                    "required": False,
                    'schema': {
                        'type': 'string',
                    },
                })
            operation['parameters'].append({
                "name": "first_name",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'string',
                },
            })
            operation['parameters'].append({
                "name": "last_name",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'string',
                },
            })
            operation['parameters'].append({
                "name": "email",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'string',
                },
            })
            operation['parameters'].append({
                "name": "is_staff",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'boolean',
                },
            })
            operation['parameters'].append({
                "name": "is_superuser",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'boolean',
                },
            })
            operation['parameters'].append({
                "name": "is_active",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'boolean',
                },
            })
        return operation


class SlpIdSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if method == 'PUT':
            operation['parameters'].append({
                "name": "active",
                "in": "form",
                "required": False,
                'schema': {
                    'type': 'boolean',
                },
            })

        return operation


class AddressSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if method == 'POST':
            operation['parameters'].append({
                "name": "alias",
                "in": "form",
                "required": True,
                'schema': {
                    'type': 'string',
                },
            })
        if method == 'PUT' or method == 'POST':
            operation['parameters'].append({
                "name": "public_key",
                "in": "form",
                "required": True,
                'schema': {
                    'type': 'string',
                },
            })
        return operation


class RawPublicationSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == 'POST':
            operation['parameters'].append({
                "name": "publication",
                "in": "form",
                "required": True,
                "description": "publication content",
                "schema": {
                    "type": "string",
                }
            })
            operation['parameters'].append({
                "name": "format",
                "in": "form",
                "required": True,
                "description": "Publication format ('json-ld' or 'n3')",
                "schema": {
                    "type": "string",
                    "default": "json-ld",
                    "enum": [
                        "json-ld", "n3"
                    ]
                }
            })
            operation['parameters'].append({
                "name": "description",
                "in": "form",
                "required": True,
                "description": "Publication description",
                "schema": {
                    "type": "string",
                }
            })
            operation['parameters'].append({
                "name": "slp_id",
                "in": "form",
                "required": False,
                "description": "Ledger ID Alias to publish with",
                "schema": {
                    "type": "string"
                }
            })
        return operation


class TransferSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['parameters'].append({
            "name": "asset_id",
            "in": "form",
            "required": True,
            "description": "Asset ID to transfer",
            "schema": {
                "type": "string"
            }
        })
        operation['parameters'].append({
            "name": "recipient",
            "in": "form",
            "required": True,
            "description": "Recipient (address alias) of asset",
            "schema": {
                "type": "string"
            }
        })
        operation['parameters'].append({
            "name": "slp_id",
            "in": "form",
            "required": False,
            "description": "Ledger ID Alias to transact with",
            "schema": {
                "type": "string"
            }
        })
        return operation

class OrderSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if method == 'POST':
            operation['parameters'] += [
                {
                    "name": "service_provider",
                    "in": "form",
                    "required": True,
                    "description": "Addressbook alias of order recipient",
                    "schema": {'type': 'string'}
                },
                {
                    'name': 'order',
                    'in': 'form',
                    'required': True,
                    'description': 'The order object',
                    'schema': {'type': 'string'}
                }
            ]

class EventSchema(AutoSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)

        if method == 'POST':
            operation['parameters'] += [
                {
                    "name": "order_asset_id",
                    "in": "form",
                    "required": True,
                    "description": "Asset ID of the related order",
                    "schema": {'type': 'string'}
                },
                {
                    'name': 'event',
                    'in': 'form',
                    'required': True,
                    'description': 'The event object',
                    'schema': {'type': 'string'}
                },
                # {
                #     'name': 'milestone',
                #     'in': 'form',
                #     'required': True,
                #     'description': 'The type of event that occurred',
                #     'schema': {'type': 'string'}
                #     # TODO multiple choice invoeren?
                # },
                # {
                #     'name': 'place',
                #     'in': 'form',
                #     'required': True,
                #     'description': 'The location at which the event occurred',
                #     'schema': {'type': 'string'}
                # },
                # {
                #     'name': 'time',
                #     'in': 'form',
                #     'required': True,
                #     'description': 'The time at which the event occurred',
                #     'schema': {'type': 'string'}
                # },
            ]