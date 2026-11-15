"""Serializer fields shared by the apps.

The database stores the Algerian wall clock (naive local time), so the API
has to say which timezone it is talking about. Otherwise a client would read
``2026-11-12T13:18:35`` as its own local time and land an hour off.
"""

from django.db import models
from rest_framework import serializers

from apps.core.time import ALGERIA


class AlgeriaDateTimeField(serializers.DateTimeField):
    """A timestamp of the shop, always sent with its offset."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("default_timezone", ALGERIA)
        super().__init__(*args, **kwargs)


class AlgeriaModelSerializer(serializers.ModelSerializer):
    """A model serializer whose datetimes carry the Algerian offset."""

    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.DateTimeField: AlgeriaDateTimeField,
    }
