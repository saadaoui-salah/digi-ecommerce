from django.contrib import admin

from .models import AnalyticsRun, SalesAggregate


@admin.register(SalesAggregate)
class SalesAggregateAdmin(admin.ModelAdmin):
    list_display = (
        "period",
        "bucket",
        "product",
        "count",
        "spend",
        "benefit",
        "updated_at",
    )
    list_filter = ("period", "product__category")
    search_fields = ("product__name", "product__slug")
    readonly_fields = ("updated_at",)
    date_hierarchy = "bucket"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "product__category")

    def has_add_permission(self, request):
        # The rows are written by the aggregation jobs, never by hand.
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AnalyticsRun)
class AnalyticsRunAdmin(admin.ModelAdmin):
    list_display = ("period", "last_bucket", "ran_at", "rows")
    list_filter = ("period",)
    readonly_fields = ("period", "last_bucket", "ran_at", "rows")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
