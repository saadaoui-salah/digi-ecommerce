from decimal import Decimal

from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Min, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import path
from django.utils.html import format_html, mark_safe
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Category,
    ItemType,
    Package,
    PackageCode,
    PackageGroup,
    Product,
    ProductImage,
    Promotion,
)


COPY_ICON = (
    '<svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<rect width="14" height="14" x="8" y="8" rx="2" ry="2" />'
    '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />'
    "</svg>"
)

CHECK_ICON = (
    '<svg class="check-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16"'
    ' viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"'
    ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M20 6 9 17l-5-5" />'
    "</svg>"
)


def copy_button(value):
    """The button that copies a value: an icon that turns into a tick."""
    return format_html(
        '<button type="button" class="copy-btn button" data-copy-code="{}"'
        ' title="Copy" style="cursor:pointer;line-height:0;padding:4px 8px">'
        "{}{}</button>",
        value,
        mark_safe(COPY_ICON),
        mark_safe(CHECK_ICON),
    )


class ActiveOnlyChangeList(ChangeList):
    """Show active rows unless the staff member explicitly filters otherwise."""

    def __init__(self, request, *args, **kwargs):
        if "is_active__exact" not in request.GET:
            params = request.GET.copy()
            params["is_active__exact"] = "1"
            request.GET = params
        super().__init__(request, *args, **kwargs)


class ActiveOnlyListMixin:
    """Default the changelist of an is_active model to active rows only."""

    def get_changelist(self, request, **kwargs):
        return ActiveOnlyChangeList


@admin.register(Category)
class CategoryAdmin(ActiveOnlyListMixin, ModelAdmin):
    list_display = (
        "name",
        "slug",
        "parent",
        "products_count",
        "sales_count",
        "total_revenue",
        "net_profit",
        "pending_demand_orders",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    autocomplete_fields = ("parent",)
    fields = (
        "name",
        "parent",
        "image",
        "is_active",
        "sales_count",
        "total_revenue",
        "net_profit",
        "total_benefit",
        "pending_demand_orders",
    )
    readonly_fields = (
        "sales_count",
        "total_revenue",
        "net_profit",
        "total_benefit",
        "pending_demand_orders",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("parent")
            .annotate(products_count=Count("products"))
        )

    @admin.display(ordering="products_count")
    def products_count(self, obj):
        return obj.products_count


class PackageInline(TabularInline):
    model = Package
    extra = 0
    autocomplete_fields = ("group",)
    fields = (
        "name",
        "group",
        "type",
        "price",
        "stock",
        "sort_order",
        "is_active",
    )
    show_change_link = True


class PackageGroupInline(TabularInline):
    model = PackageGroup
    extra = 0
    fields = ("name", "sort_order", "is_active")
    show_change_link = True


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "sort_order")


@admin.register(Promotion)
class PromotionAdmin(ModelAdmin):
    list_display = (
        "name",
        "product",
        "category",
        "percentage",
        "discounted_price",
        "base_price",
        "is_current",
        "is_active",
        "ends_at",
    )
    list_filter = ("is_active", "category")
    search_fields = ("name", "product__name", "category__name")
    autocomplete_fields = ("product", "category")
    readonly_fields = ("base_price", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("name", "product", "category", "is_active"),
                "description": (
                    "Apply the promotion to a product or to a whole category."
                ),
            },
        ),
        (
            "Discount",
            {
                "fields": ("percentage", "discounted_price", "base_price"),
                "description": (
                    "Fill in the percentage or the discounted price — the other "
                    "one is calculated from the original price."
                ),
            },
        ),
        ("Schedule", {"fields": ("starts_at", "ends_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product", "category")
        )

    @admin.display(description="Original price")
    def base_price(self, obj):
        return obj.base_price

    @admin.display(boolean=True)
    def is_current(self, obj):
        return obj.is_current

    def save_model(self, request, obj, form, change):
        # The field the admin typed wins, the other one is calculated.
        if request.POST.get("percentage"):
            obj.percentage = form.cleaned_data.get("percentage")
            obj.discounted_price = None
        elif request.POST.get("discounted_price"):
            obj.discounted_price = form.cleaned_data.get("discounted_price")
            obj.percentage = None
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(ActiveOnlyListMixin, ModelAdmin):
    # The package sections are heavy, so they are fetched as HTML fragments
    # after the change form opens. The fragments are real inline formsets, so
    # Save / Add another / Remove keep working exactly as before.
    change_form_template = "admin/catalog/product/change_form.html"
    lazy_inlines = (PackageGroup, Package)
    lazy_inline_per_page = 5

    list_display = (
        "name",
        "type",
        "category",
        "price_from",
        "sales_count",
        "total_revenue",
        "net_profit",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "type", "requires_info", "category")
    search_fields = ("name", "short_description")
    autocomplete_fields = ("category",)
    inlines = (ProductImageInline, PackageGroupInline, PackageInline)
    readonly_fields = (
        "sales_count",
        "total_revenue",
        "net_profit",
        "total_benefit",
        "pending_demand_orders",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category")
            .annotate(
                price_from_value=Min(
                    "packages__price", filter=Q(packages__is_active=True)
                )
            )
        )

    @admin.display(description="Price from", ordering="price_from_value")
    def price_from(self, obj):
        value = obj.price_from_value
        if value is None:
            return "—"
        # SQLite hands the smallest price back as a float, so it is written
        # out by hand: 27.99 and never 27.99000000000000.
        return f"{Decimal(value):.2f} DA"

    # --- Lazy inline fragments ------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()
        lazy_urls = [
            path(
                "<int:object_id>/inline/packagegroup/",
                self.admin_site.admin_view(self.packagegroup_inline),
                name="catalog_product_packagegroup_inline",
            ),
            path(
                "<int:object_id>/inline/package/",
                self.admin_site.admin_view(self.package_inline),
                name="catalog_product_package_inline",
            ),
        ]
        return lazy_urls + urls

    def packagegroup_inline(self, request, object_id):
        return self._render_lazy_inline(request, object_id, PackageGroup)

    def package_inline(self, request, object_id):
        return self._render_lazy_inline(request, object_id, Package)

    def _render_lazy_inline(self, request, object_id, model):
        if request.method != "GET":
            raise Http404
        product = get_object_or_404(Product, pk=object_id)
        if not self.has_change_permission(request, product):
            raise PermissionDenied

        # Build the formsets exactly as the change view does. An unbound
        # formset on GET uses the product's related objects as initial data.
        formsets, inline_instances = self._create_formsets(
            request, product, change=True
        )
        wrappers = self.get_inline_formsets(
            request, formsets, inline_instances, product
        )
        wrapper = next((w for w in wrappers if w.opts.model is model), None)
        if wrapper is None:
            raise Http404

        total = len(wrapper.formset.initial_forms)
        html = render_to_string(
            "admin/catalog/product/inline_fragment.html",
            {
                "inline_admin_formset": wrapper,
                "per_page": self.lazy_inline_per_page,
                "hidden_count": max(0, total - self.lazy_inline_per_page),
            },
            request=request,
        )
        return HttpResponse(html)


@admin.register(PackageGroup)
class PackageGroupAdmin(ActiveOnlyListMixin, ModelAdmin):
    list_display = ("product", "name", "packages_count", "is_active")
    list_filter = ("is_active", "product__category")
    search_fields = ("name", "product__name")
    autocomplete_fields = ("product",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product")
            .annotate(packages_count=Count("packages"))
        )

    @admin.display(ordering="packages_count")
    def packages_count(self, obj):
        return obj.packages_count


class PackageCodeInline(TabularInline):
    model = PackageCode
    extra = 1
    fields = ("code", "is_used", "claimed_by", "claimed_at")
    readonly_fields = ("claimed_at",)
    autocomplete_fields = ("claimed_by",)


@admin.register(Package)
class PackageAdmin(ActiveOnlyListMixin, ModelAdmin):
    list_display = (
        "product",
        "group",
        "name",
        "type",
        "price",
        "cost",
        "margin_display",
        "sales_count",
        "total_revenue",
        "net_profit",
        "stock_display",
        "stock_worth_display",
        "codes_left",
        "is_active",
    )
    list_filter = ("is_active", "type", "product__category")
    search_fields = ("name", "product__name")
    autocomplete_fields = ("product", "group")
    inlines = (PackageCodeInline,)
    readonly_fields = (
        "sales_count",
        "total_revenue",
        "net_profit",
        "total_benefit",
        "margin_display",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ("product", "group", "name", "type", "price"),
            },
        ),
        (
            "Cost and margin",
            {
                "fields": ("cost", "margin_display"),
                "description": (
                    "Fill in what you paid for this package: the profit of "
                    "every sale is the price minus this cost."
                ),
            },
        ),
        (
            "Delivery",
            {
                "fields": ("stock", "sort_order", "is_active"),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("product", "group")
            .annotate(
                unused_codes=Count("codes", filter=Q(codes__is_used=False)),
                total_codes=Count("codes"),
            )
        )

    @admin.display(description="Margin", ordering="price")
    def margin_display(self, obj):
        if obj.cost is None:
            return "—"
        return f"{obj.margin:.2f} DA"

    @admin.display(boolean=True)
    def is_available(self, obj):
        return obj.is_available

    @admin.display(description="Stock", ordering="stock")
    def stock_display(self, obj):
        if obj.type == ItemType.IMMEDIATE:
            # The stock of an instant package is the number of codes it holds.
            return obj.unused_codes
        return "unlimited" if obj.stock is None else obj.stock

    @admin.display(description="Stock worth", ordering="stock")
    def stock_worth_display(self, obj):
        if obj.type != ItemType.IMMEDIATE:
            return "—"
        return f"{Decimal(obj.stock or 0) * Decimal(obj.price):.2f} DA"

    @admin.display(description="Codes", ordering="total_codes")
    def codes_left(self, obj):
        if obj.type != ItemType.IMMEDIATE:
            return "—"
        return f"{obj.unused_codes} / {obj.total_codes}"


@admin.register(PackageCode)
class PackageCodeAdmin(ModelAdmin):
    list_display = (
        "id",
        "package",
        "code_copy",
        "is_used",
        "claimed_by_copy",
        "claimed_at",
    )
    list_filter = ("is_used",)
    search_fields = ("code", "package__name", "claimed_by__email")
    autocomplete_fields = ("package", "claimed_by")
    readonly_fields = ("claimed_at",)
    change_list_template = "admin/catalog/packagecode/change_list.html"

    @admin.display(description="Code")
    def code_copy(self, obj):
        """The credentials of the code and the button that copies them."""
        return format_html(
            '<div style="align-items:center;display:flex;gap:8px">'
            '<span style="font-family:monospace;white-space:nowrap">{}</span>{}</div>',
            obj.code,
            copy_button(obj.code),
        )

    @admin.display(description="Claimed by", ordering="claimed_by__email")
    def claimed_by_copy(self, obj):
        if obj.claimed_by_id is None:
            return "—"
        return format_html(
            '<div style="align-items:center;display:flex;gap:8px">'
            '<span style="white-space:nowrap">{}</span>{}</div>',
            obj.claimed_by.get_username(),
            copy_button(obj.claimed_by.email),
        )
