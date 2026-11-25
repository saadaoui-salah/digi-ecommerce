"""Serializers for the analytics figures."""

from rest_framework import serializers


class AnalyticsProductSerializer(serializers.Serializer):
    """One product of the bar chart: how often it was bought and what it made."""

    product = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    product_slug = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    count = serializers.IntegerField(read_only=True)
    spend = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    benefit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    def get_product(self, obj):
        return obj["product"].pk

    def get_product_name(self, obj):
        return obj["product"].name

    def get_product_slug(self, obj):
        return obj["product"].slug

    def get_category_name(self, obj):
        product = obj["product"]
        return product.category.name if product.category_id else ""


class AnalyticsBucketSerializer(serializers.Serializer):
    """One point of the spend and benefit lines."""

    bucket = serializers.DateField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    spend = serializers.CharField(read_only=True)
    benefit = serializers.CharField(read_only=True)
