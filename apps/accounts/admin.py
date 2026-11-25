from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path
from django.core.exceptions import PermissionDenied
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm

from apps.catalog.models import PackageCode

from .forms import UserChangeForm, UserCreationForm
from .models import (
    Notification,
    Order,
    OrderReport,
    OrderStatus,
    Transaction,
    User,
)
from .models import (
    Daira,
    Coupon,
    Credit,
    CreditKind,
    Notification,
    NotificationKind,
    Order,
    OrderReport,
    OrderStatus,
    Referral,
    Region,
    Transaction,
    User,
    Wilaya,
)
from .services import assign_order, change_status, notify


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = (
        "username",
        "email",
        "credit",
        "is_approved",
        "is_sub_admin",
        "is_staff",
        "stock_worth",
        "accepts_referrals",
        "referral_percentage",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_approved", "is_sub_admin", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
    autocomplete_fields = ("wilaya", "daira")
    readonly_fields = (
        "total_revenue",
        "net_profit",
        "net_profit_percentage",
        "total_benefit",
        "orders_count",
        "pending_demand_orders",
        "stock_worth",
        "stock_quantity",
        "referral_code",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "wilaya",
                    "daira",
                ),
            },
        ),
        (
            "Billing",
            {
                "fields": ("credit", "free_spend"),
                "description": (
                    "Tick the box to let this customer buy with a zero "
                    "balance: the storefront reads Unlimited and the purchase "
                    "is recorded as credit they owe."
                ),
            },
        ),
        ("Role", {"fields": ("is_sub_admin",)}),
        (
            "Approval",
            {
                "fields": ("is_approved", "approved_at"),
                "description": "New accounts stay unapproved until a staff member approves them.",
            },
        ),
        (
            "Shop figures",
            {
                "fields": (
                    "total_revenue",
                    "net_profit",
                    "net_profit_percentage",
                    "total_benefit",
                    "orders_count",
                    "pending_demand_orders",
                    "stock_worth",
                    "stock_quantity",
                ),
                "description": (
                    "Kept up to date by the signals. The stock worth and the "
                    "stock quantity are figures of the shop — the codes that "
                    "are still unsold — so only the staff accounts carry them."
                ),
            },
        ),
        (
            "Referrals",
            {
                "fields": (
                    "accepts_referrals",
                    "referral_percentage",
                    "referral_code",
                    "referred_by",
                ),
                "description": (
                    "Tick the box on the customers who are willing to receive "
                    "referrals and say how much of every referred order they "
                    "earn. Their code goes in the link they share."
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "credit",
                    "is_sub_admin",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        was_approved = False
        if change:
            was_approved = (
                User.objects.filter(pk=obj.pk, is_approved=True).exists()
            )
        super().save_model(request, obj, form, change)
        # Tell the customer as soon as their account is approved.
        if obj.is_approved and not was_approved:
            notify(
                obj,
                NotificationKind.ACCOUNT_APPROVED,
                "Your account has been approved",
                "Your account is approved — you can now browse the catalog and place orders.",
            )


@admin.register(OrderReport)
class OrderReportAdmin(ModelAdmin):
    list_display = (
        "id",
        "order",
        "title",
        "author",
        "created_at",
    )
    search_fields = ("title", "details", "order__product_name", "author__email")
    autocomplete_fields = ("order", "author")
    readonly_fields = ("created_at",)


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("id", "recipient", "kind", "title", "order", "is_read", "created_at")
    list_filter = ("kind", "is_read")
    search_fields = ("title", "body", "recipient__email")
    autocomplete_fields = ("recipient", "order")
    readonly_fields = ("created_at",)


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "product_name",
        "package_name",
        "group_name",
        "price",
        "sold_price",
        "status",
        "assigned_to",
        "code_masked",
        "created_at",
    )
    list_filter = ("status", "assigned_to", "created_at")
    search_fields = ("user__email", "user__username", "product_name", "package_name")
    autocomplete_fields = ("user", "product", "package", "group", "code", "assigned_to")
    readonly_fields = ("created_at", "code_masked", "assigned_at", "sold_at")
    actions = ("attach_code",)
    change_list_template = "admin/accounts/order/change_list.html"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "product",
                    "package",
                    "group",
                    "price",
                    "status",
                )
            },
        ),
        (
            "Handling",
            {
                "fields": ("assigned_to", "assigned_at", "code", "code_masked"),
            },
        ),
        (
            "Resale",
            {
                "fields": ("sold_price", "sold_at"),
                "description": (
                    "What the customer resold this order for, recorded from "
                    "their orders page."
                ),
            },
        ),
        (
            "Buyer information",
            {
                "fields": ("buyer_info",),
                "description": (
                    "Details the buyer typed into the pre-order popup for "
                    "on-demand products that require extra information."
                ),
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "processing/",
                self.admin_site.admin_view(self.processing_view),
                name="accounts_order_processing",
            ),
        ]
        return custom + urls

    def processing_view(self, request):
        """Custom page to work through the on-demand orders."""
        orders = (
            Order.objects.filter(
                status__in=(
                    OrderStatus.PENDING,
                    OrderStatus.IN_PROGRESS,
                    OrderStatus.HAS_PROBLEMS,
                )
            )
            .select_related("user", "package", "group", "assigned_to")
            .order_by("status", "created_at")
        )

        if request.method == "POST":
            order_id = request.POST.get("order_id")
            action = request.POST.get("action")
            order = Order.objects.filter(pk=order_id).first()
            if order is None:
                messages.error(request, "Order not found.")
            elif action == "take":
                assign_order(order, request.user)
                messages.success(request, f"Order #{order.pk} is yours now.")
            elif action == "status":
                status = request.POST.get("status")
                report = None
                title = (request.POST.get("report_title") or "").strip()
                details = (request.POST.get("report_details") or "").strip()
                if status == OrderStatus.HAS_PROBLEMS and title:
                    report = OrderReport.objects.create(
                        order=order,
                        author=request.user,
                        title=title,
                        details=details,
                    )
                try:
                    change_status(
                        order,
                        status,
                        admin=request.user,
                        report=report,
                        note=(request.POST.get("note") or "").strip(),
                    )
                    messages.success(request, f"Order #{order.pk} updated.")
                except ValueError as error:
                    messages.error(request, str(error))
            return HttpResponseRedirect("../processing/")

        context = {
            **self.admin_site.each_context(request),
            "title": "On-demand orders",
            "orders": orders,
            "statuses": OrderStatus.choices,
            "opts": self.model._meta,
        }
        return TemplateResponse(request, "admin/accounts/order/processing.html", context)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "product", "package", "group", "code")
        )

    @admin.display(description="Code")
    def code_masked(self, obj):
        return obj.code_masked

    @admin.action(description="Attach the next available code")
    def attach_code(self, request, queryset):
        attached = 0
        for order in queryset.filter(code__isnull=True).select_related("package"):
            code = (
                PackageCode.objects.filter(
                    package=order.package, is_used=False
                )
                .order_by("created_at", "id")
                .first()
            )
            if code is None:
                continue
            code.is_used = True
            code.claimed_by = order.user
            code.claimed_at = order.created_at
            code.save(update_fields=["is_used", "claimed_by", "claimed_at"])
            order.code = code
            order.status = OrderStatus.DELIVERED
            order.save(update_fields=["code", "status"])
            attached += 1

        self.message_user(request, f"{attached} order(s) got a code.")


class DairaInline(TabularInline):
    model = Daira
    extra = 1
    fields = ("name", "is_active")
    autocomplete_fields = ()


class WilayaInline(TabularInline):
    model = Wilaya
    extra = 1
    fields = ("name", "is_active")
    autocomplete_fields = ()


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    """The regions of the country and the wilayas they hold.

    Wilayas are attached by picking dairas in the search box: a daira's
    wilaya gets this region as its FK. The current members are loaded as a
    separate HTML fragment so a region with many dairas stays fast.
    """

    change_form_template = "admin/accounts/region/change_form.html"
    dairas_per_page = 5

    list_display = ("name", "wilayas_count", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(wilayas_count=Count("wilayas"))

    @admin.display(ordering="wilayas_count")
    def wilayas_count(self, obj):
        return obj.wilayas_count

    # --- AJAX endpoints for the wilaya/daira picker ---------------------------

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:object_id>/dairas/",
                self.admin_site.admin_view(self.dairas_view),
                name="accounts_region_dairas",
            ),
            path(
                "<int:object_id>/search-dairas/",
                self.admin_site.admin_view(self.search_dairas),
                name="accounts_region_search_dairas",
            ),
            path(
                "<int:object_id>/add-daira/",
                self.admin_site.admin_view(self.add_daira),
                name="accounts_region_add_daira",
            ),
            path(
                "<int:object_id>/remove-wilaya/",
                self.admin_site.admin_view(self.remove_wilaya),
                name="accounts_region_remove_wilaya",
            ),
        ]
        return custom + urls

    def _region(self, request, object_id):
        region = get_object_or_404(Region, pk=object_id)
        if not self.has_change_permission(request, region):
            raise PermissionDenied
        return region

    def dairas_view(self, request, object_id):
        if request.method != "GET":
            raise PermissionDenied
        region = self._region(request, object_id)

        rows = []
        wilayas = region.wilayas.prefetch_related("dairas").order_by("name")
        for wilaya in wilayas:
            for daira in wilaya.dairas.all():
                rows.append({"wilaya": wilaya, "daira": daira})

        html = render_to_string(
            "admin/accounts/region/dairas_fragment.html",
            {
                "region": region,
                "rows": rows,
                "per_page": self.dairas_per_page,
                "hidden_count": max(0, len(rows) - self.dairas_per_page),
            },
            request=request,
        )
        return HttpResponse(html)

    def search_dairas(self, request, object_id):
        if request.method != "GET":
            raise PermissionDenied
        region = self._region(request, object_id)
        term = request.GET.get("q", "").strip()

        results = []
        if len(term) >= 2:
            queryset = Daira.objects.filter(name__icontains=term).select_related(
                "wilaya"
            ).order_by("name")[:10]
            for daira in queryset:
                results.append(
                    {
                        "id": daira.id,
                        "name": daira.name,
                        "wilaya_id": daira.wilaya_id,
                        "wilaya": daira.wilaya.name,
                        "assigned": daira.wilaya.region_id == region.id,
                    }
                )
        return JsonResponse({"results": results})

    def add_daira(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied
        region = self._region(request, object_id)
        daira = get_object_or_404(Daira, pk=request.POST.get("daira_id"))
        wilaya = daira.wilaya

        already = wilaya.region_id == region.id
        if not already:
            wilaya.region = region
            wilaya.save(update_fields=["region"])

        self.message_user(
            request,
            (
                f"{wilaya.name} is already in {region.name}."
                if already
                else f"Added {wilaya.name} to {region.name}."
            ),
            level=messages.INFO,
        )
        return JsonResponse({"ok": True, "already": already, "wilaya": wilaya.name})

    def remove_wilaya(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied
        region = self._region(request, object_id)
        wilaya = get_object_or_404(
            Wilaya, pk=request.POST.get("wilaya_id"), region=region
        )
        wilaya.region = None
        wilaya.save(update_fields=["region"])

        self.message_user(
            request, f"Removed {wilaya.name} from {region.name}.", level=messages.INFO
        )
        return JsonResponse({"ok": True})


@admin.register(Wilaya)
class WilayaAdmin(ModelAdmin):
    list_display = ("name", "region", "dairas_count", "is_active")
    list_filter = ("is_active", "region")
    search_fields = ("name", "region__name")
    autocomplete_fields = ("region",)
    inlines = (DairaInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            dairas_count=Count("dairas")
        )

    @admin.display(ordering="dairas_count")
    def dairas_count(self, obj):
        return obj.dairas_count


@admin.register(Daira)
class DairaAdmin(ModelAdmin):
    list_display = ("name", "wilaya", "is_active")
    list_filter = ("is_active", "wilaya")
    search_fields = ("name", "wilaya__name")
    autocomplete_fields = ("wilaya",)


@admin.register(Coupon)
class CouponAdmin(ModelAdmin):
    """The coupons of the customers.

    The staff fill in **either** a percentage **or** a discounted price: the
    other one is filled in for them, from the price of the product.
    """

    list_display = (
        "code",
        "user",
        "product",
        "percentage",
        "discount_price",
        "max_orders",
        "used_orders",
        "is_active",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_active", "product")
    search_fields = ("code", "user__email", "user__username", "product__name")
    autocomplete_fields = ("user", "product")
    readonly_fields = ("code", "used_orders", "created_at")
    fieldsets = (
        (
            None,
            {
                "fields": ("user", "product", "code", "max_orders", "is_active"),
                "description": (
                    "The code is generated on its own. The coupon can be used "
                    "for as many orders as the limit says."
                ),
            },
        ),
        (
            "The discount",
            {
                "fields": ("percentage", "discount_price"),
                "description": (
                    "Fill in the percentage or the price the customer pays — "
                    "the other one is filled in for you."
                ),
            },
        ),
        ("Details", {"fields": ("expires_at", "used_orders", "created_at")}),
    )

    class Media:
        css = {"all": ("admin/css/coupon.css",)}
        js = ("admin/js/coupon.js",)


@admin.register(Referral)
class ReferralAdmin(ModelAdmin):
    """What the customers earned from the customers they referred."""

    list_display = (
        "referrer",
        "referred",
        "order",
        "amount",
        "percentage",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("referrer__email", "referred__email", "order__product_name")
    autocomplete_fields = ("referrer", "referred", "order")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        # The rows are written by the order signal, never by hand.
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Credit)
class CreditAdmin(ModelAdmin):
    list_display = ("id", "user", "kind", "amount", "note", "order", "created_by", "created_at")
    list_filter = ("kind", "created_at")
    search_fields = ("user__email", "user__username", "note")
    autocomplete_fields = ("user", "order", "created_by")
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            None,
            {
                "fields": ("user", "kind", "amount", "note"),
                "description": (
                    "A top-up adds this amount to the customer's balance when "
                    "you save it. A free-spend row only records what they "
                    "owe and leaves the balance alone."
                ),
            },
        ),
        ("Links", {"fields": ("order", "created_by", "created_at")}),
    )

    def save_model(self, request, obj, form, change):
        if obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "order", "created_by")


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "kind",
        "amount",
        "balance_after",
        "method",
        "created_by",
        "created_at",
    )
    list_filter = ("kind", "method")
    search_fields = ("user__email", "user__username", "note")
    autocomplete_fields = ("user", "created_by")
    readonly_fields = ("balance_after", "created_at")

    fieldsets = (
        (
            None,
            {
                "fields": ("user", "kind", "amount", "method", "note"),
                "description": (
                    "Creating a credit or refund transaction increases the "
                    "customer balance; a debit decreases it."
                ),
            },
        ),
        ("Details", {"fields": ("balance_after", "created_by", "created_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "created_by")

    @admin.display(ordering="-created_at")
    def created_at(self, obj):
        return obj.created_at
