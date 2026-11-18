import secrets
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from apps.core.time import now as algeria_now


class TransactionKind(models.TextChoices):
    ORDER = "order", "Order purchase"
    CREDIT = "credit", "Credit purchased"
    REFUND = "refund", "Refund"
    REFERRAL = "referral", "Referral"


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In progress"
    HAS_PROBLEMS = "has_problems", "Has problems"
    DELIVERED = "delivered", "Delivered"
    REFUNDED = "refunded", "Refunded"
    CANCELLED = "cancelled", "Cancelled"


class NotificationKind(models.TextChoices):
    ORDER_PLACED = "order_placed", "Order placed"
    ORDER_ASSIGNED = "order_assigned", "Order assigned"
    STATUS_CHANGED = "status_changed", "Status changed"
    ORDER_DELIVERED = "order_delivered", "Order delivered"
    REPORT_CREATED = "report_created", "Report created"
    ACCOUNT_APPROVED = "account_approved", "Account approved"
    CREDIT_TOPUP = "credit_topup", "Credit top-up"
    REFERRAL = "referral", "Referral"


class Region(models.Model):
    """A region of the country.

    It holds the wilayas, and every wilaya holds its dairas — the way the
    country is divided.
    """

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "regions"

    def __str__(self):
        return self.name


class Wilaya(models.Model):
    """A wilaya — a state — of a region."""

    name = models.CharField(max_length=100)
    # Regions are optional: staff can group wilayas into regions later from
    # the admin instead of having to do it before importing the geo data.
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="wilayas",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("region__name", "name")
        verbose_name_plural = "wilayas"
        constraints = [
            models.UniqueConstraint(
                fields=("region", "name"), name="accounts_wilaya_unique_per_region"
            )
        ]

    def __str__(self):
        return f"{self.name} — {self.region.name}"


class Daira(models.Model):
    """A daira — a province — of a wilaya."""

    name = models.CharField(max_length=100)
    wilaya = models.ForeignKey(
        Wilaya, on_delete=models.PROTECT, related_name="dairas"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("wilaya__name", "name")
        verbose_name_plural = "dairas"
        constraints = [
            models.UniqueConstraint(
                fields=("wilaya", "name"), name="accounts_daira_unique_per_wilaya"
            )
        ]

    def __str__(self):
        return f"{self.name} — {self.wilaya.name}"


class User(AbstractUser):
    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    free_spend = models.BooleanField(
        default=False,
        help_text=(
            "Buy even with a zero balance: the balance reads Unlimited in the "
            "storefront and the purchase is recorded as credit owed. Only "
            "staff can set this."
        ),
    )
    # Counters of the customer's activity. They are kept up to date by the
    # order signals, so the dashboard never has to walk the orders.
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Everything the customer has paid for their orders.",
    )
    net_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=(
            "What the store earned on their orders: the price minus the "
            "cost of the package."
        ),
    )
    total_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=(
            "What the customer earned by reselling: the resale price minus "
            "what they paid."
        ),
    )
    orders_count = models.PositiveIntegerField(
        default=0, help_text="How many orders the customer placed."
    )
    pending_demand_orders = models.PositiveIntegerField(
        default=0,
        help_text=(
            "How many of their on-demand orders are still waiting to be "
            "delivered."
        ),
    )
    stock_worth = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=(
            "The worth of the stock the shop has not sold yet. It is a "
            "figure of the shop, so only the staff accounts carry it and the "
            "admin dashboard is the one that reads it."
        ),
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text=(
            "How many codes are still waiting to be sold. Like the worth, it "
            "is a figure of the shop, so only the staff accounts carry it."
        ),
    )
    net_profit_percentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=(
            "The net profit as a percentage of what the customer paid: the "
            "price of the packages sold minus their cost, over the price of "
            "the packages sold. The signals keep it up to date."
        ),
    )
    phone = models.CharField(max_length=20, blank=True)
    is_sub_admin = models.BooleanField(
        default=False, help_text="Staff member who handles on-demand orders."
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="New accounts wait for an admin approval before they can browse.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    # The referral program: the staff tick the box on the accounts that are
    # willing to receive referrals and say how much they earn from them.
    accepts_referrals = models.BooleanField(
        default=False,
        help_text=(
            "The customer is willing to receive referrals: their link is "
            "shown in their account and they earn on every referred order."
        ),
    )
    referral_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="How much of every referred order they earn, in percent.",
    )
    referral_code = models.CharField(
        max_length=12,
        unique=True,
        blank=True,
        editable=False,
        help_text="The code of their referral link. It is generated on its own.",
    )
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_users",
        help_text="The customer who referred this one.",
    )
    wilaya = models.ForeignKey(
        Wilaya,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
        help_text="The wilaya the customer lives in.",
    )
    daira = models.ForeignKey(
        Daira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customers",
        help_text="The daira the customer lives in.",
    )

    class Meta(AbstractUser.Meta):
        # The columns the admin searches in and sorts by. They are indexed so
        # the lists of the admin stay quick as the shop grows. The flags are
        # left out: they hold a handful of values each, so an index on them
        # would not tell the database much.
        indexes = [
            models.Index(fields=("email",), name="accounts_user_email_idx"),
            models.Index(fields=("phone",), name="accounts_user_phone_idx"),
            models.Index(fields=("first_name",), name="accounts_user_first_idx"),
            models.Index(fields=("last_name",), name="accounts_user_last_name_idx"),
            models.Index(fields=("credit",), name="accounts_user_credit_idx"),
            models.Index(fields=("date_joined",), name="accounts_user_joined_idx"),
        ]

    def save(self, *args, **kwargs):
        if self.is_sub_admin:
            self.is_staff = True
        if not self.referral_code:
            self.referral_code = self._unique_referral_code()
        super().save(*args, **kwargs)

    def _unique_referral_code(self) -> str:
        """A code for the referral link, unique among the customers."""
        base = "REF" + secrets.token_hex(4).upper()
        code = base
        number = 2
        while type(self).objects.filter(referral_code=code).exclude(pk=self.pk).exists():
            code = f"{base}{number}"
            number += 1
        return code

    def __str__(self):
        return self.username


class Transaction(models.Model):
    """A credit movement on a customer account.

    Creating one with the `credit` or `refund` kind tops the customer's
    balance up; `debit` takes credit away. The balance after the movement is
    stored so the customer history can be read without replaying it.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    kind = models.CharField(
        max_length=20, choices=TransactionKind.choices, default=TransactionKind.CREDIT
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Always positive — the kind decides the direction.",
    )
    balance_after = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    method = models.CharField(
        max_length=60, blank=True, help_text="e.g. Bank transfer, Cash, Card."
    )
    note = models.CharField(max_length=255, blank=True)
    order = models.ForeignKey(
        "accounts.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        help_text="The order this movement paid for, when there is one.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions",
    )
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "transactions"
        # The columns the admin filters by and sorts by.
        indexes = [
            models.Index(fields=("kind",), name="accounts_tx_kind_idx"),
            models.Index(fields=("method",), name="accounts_tx_method_idx"),
            models.Index(fields=("created_at",), name="accounts_tx_created_idx"),
        ]

    def __str__(self):
        return f"{self.user} {self.kind} {self.amount} DA"

    @property
    def signed_amount(self):
        """Order purchases take credit away, everything else adds it."""
        if self.kind == TransactionKind.ORDER:
            return -Decimal(self.amount)
        return Decimal(self.amount)

    @property
    def product_name(self):
        """The product this movement belongs to, when it paid for an order."""
        if self.order_id is None:
            return ""
        return self.order.product_name

    @property
    def package_name(self):
        """The package this movement belongs to, when it paid for an order."""
        if self.order_id is None:
            return ""
        return self.order.package_name

    @property
    def group_name(self):
        """The sub package (the country of a grouped product)."""
        if self.order_id is None:
            return ""
        return self.order.group_name

    @property
    def detail(self):
        """What the history shows: the product and the package it paid for."""
        parts = [self.product_name, self.package_name]
        names = " · ".join(part for part in parts if part)
        if names:
            return names
        return " · ".join(part for part in (self.method, self.note) if part)

    def save(self, *args, **kwargs):
        """Apply the movement to the customer's credit balance."""
        with transaction.atomic():
            previous_delta = Decimal("0.00")
            if self.pk:
                stored = (
                    Transaction.objects.filter(pk=self.pk)
                    .values_list("kind", "amount")
                    .first()
                )
                if stored:
                    kind, amount = stored
                    previous_delta = (
                        -Decimal(amount)
                        if kind == TransactionKind.ORDER
                        else Decimal(amount)
                    )

            super().save(*args, **kwargs)

            delta = self.signed_amount - previous_delta
            if delta == 0:
                return

            account = User.objects.select_for_update().get(pk=self.user_id)
            # A balance never goes below zero — free-spend customers owe the
            # difference instead (see the Credit model).
            account.credit = max(Decimal("0.00"), account.credit + delta)
            account.save(update_fields=["credit"])

            self.balance_after = account.credit
            Transaction.objects.filter(pk=self.pk).update(balance_after=account.credit)


class CreditKind(models.TextChoices):
    DEBT = "debt", "Free spend"
    TOPUP = "topup", "Admin top-up"
    REFERRAL = "referral", "Referral"


class Credit(models.Model):
    """What a customer owes the store, or what the store granted them.

    Two rows kinds:

    * ``debt`` — a free-spend customer bought with an empty balance. The
      balance itself never goes negative; the shortfall is recorded here.
    * ``topup`` — staff granted credit. A signal adds the amount to the
      customer's balance, and only when the row is created (order-side rows
      are always ``debt``, so the signal never fires for them).
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="credits"
    )
    kind = models.CharField(
        max_length=20, choices=CreditKind.choices, default=CreditKind.DEBT
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Always positive — the kind decides the direction.",
    )
    note = models.CharField(max_length=255, blank=True)
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="credits",
        help_text="The order that ran the balance down to zero.",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_credits",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "credits"
        # The columns the admin filters by and sorts by.
        indexes = [
            models.Index(fields=("kind",), name="accounts_credit_kind_idx"),
            models.Index(fields=("created_at",), name="accounts_credit_created_idx"),
        ]

    def __str__(self):
        return f"{self.user} {self.kind} {self.amount} DA"


class Coupon(models.Model):
    """A discount one customer can use on the orders of a product.

    The staff fills in **either** a percentage **or** a discounted price and
    the other one is filled in for them, from the price of the product. The
    code is generated on its own and the customer sees it, with the real and
    the discounted price, on the page of the product.
    """

    code = models.CharField(max_length=16, unique=True, blank=True, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="coupons",
        help_text="The customer this coupon belongs to.",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="coupons",
        help_text="The product the coupon applies to.",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="The discount in percent. Fill this one or the price below.",
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=(
            "The price the customer pays. Fill this one or the percentage "
            "above."
        ),
    )
    max_orders = models.PositiveIntegerField(
        default=1,
        help_text="How many orders the coupon can be used for.",
    )
    used_orders = models.PositiveIntegerField(
        default=0, help_text="How many orders it has been used for already."
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "coupons"
        indexes = [
            models.Index(fields=("user",), name="accounts_coupon_user_idx"),
            models.Index(fields=("product",), name="accounts_coupon_product_idx"),
            models.Index(fields=("created_at",), name="accounts_coupon_created_idx"),
        ]

    def __str__(self):
        return f"{self.code} — {self.user}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._unique_code()
        self._fill_the_other_price()
        super().save(*args, **kwargs)

    def _unique_code(self) -> str:
        """A code for the coupon, unique among the coupons."""
        base = "DIGI" + secrets.token_hex(3).upper()
        code = base
        number = 2
        while type(self).objects.filter(code=code).exclude(pk=self.pk).exists():
            code = f"{base}{number}"
            number += 1
        return code

    @property
    def reference_price(self) -> Decimal:
        """The price the two figures are calculated from.

        It is the cheapest package of the product — the price the customer
        would pay without a coupon.
        """
        price = (
            self.product.packages.filter(is_active=True)
            .order_by("price")
            .values_list("price", flat=True)
            .first()
        )
        return Decimal(price or 0)

    def _fill_the_other_price(self):
        """Fill in the figure the staff did not type.

        A percentage gives the discounted price of the reference price, and a
        discounted price gives the percentage it stands for.
        """
        reference = self.reference_price

        if self.percentage is not None and not self.discount_price:
            self.discount_price = (
                reference * (Decimal("100") - self.percentage) / Decimal("100")
            ).quantize(Decimal("0.01"))
        elif self.discount_price is not None and not self.percentage and reference:
            self.percentage = (
                (reference - self.discount_price) / reference * Decimal("100")
            ).quantize(Decimal("0.01"))

    @property
    def is_usable(self) -> bool:
        """Whether the coupon can still be used."""
        if not self.is_active:
            return False
        if self.used_orders >= self.max_orders:
            return False
        if self.expires_at and self.expires_at <= algeria_now():
            return False
        return True

    def price_for(self, price) -> Decimal:
        """The price the customer pays for a package that costs ``price``."""
        price = Decimal(price)
        if self.percentage is not None:
            return (
                price * (Decimal("100") - self.percentage) / Decimal("100")
            ).quantize(Decimal("0.01"))
        if self.discount_price is not None:
            return min(price, Decimal(self.discount_price))
        return price

    def use(self):
        """Count the order the coupon was used for."""
        self.used_orders += 1
        if self.used_orders >= self.max_orders:
            self.is_active = False
        self.save(update_fields=["used_orders", "is_active"])


class Referral(models.Model):
    """What a customer earned from an order a referred customer placed."""

    referrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals_given",
        help_text="The customer who referred the other one.",
    )
    referred = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="referrals_received",
        help_text="The customer who was referred.",
    )
    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        related_name="referrals",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="What the referrer earned from that order.",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="The percentage it was, at the time of the order.",
    )
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "referrals"
        indexes = [
            models.Index(fields=("referrer",), name="accounts_ref_referrer_idx"),
            models.Index(fields=("referred",), name="accounts_ref_referred_idx"),
            models.Index(fields=("created_at",), name="accounts_ref_created_idx"),
        ]

    def __str__(self):
        return f"{self.referrer} ← {self.referred}: {self.amount} DA"


class Order(models.Model):
    """A purchase of one package.

    Every order is linked to the code it delivers: instant packages claim a
    code straight away, on-demand packages get one attached by staff.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    package = models.ForeignKey(
        "catalog.Package",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    group = models.ForeignKey(
        "catalog.PackageGroup",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="Sub package, e.g. the country of a grouped product.",
    )
    code = models.OneToOneField(
        "catalog.PackageCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
        help_text="A code is delivered to one order only.",
    )
    # Snapshots keep the history readable when the catalog changes.
    product_name = models.CharField(max_length=200)
    product_slug = models.SlugField(max_length=200, blank=True)
    category_name = models.CharField(max_length=100, blank=True)
    package_name = models.CharField(max_length=100, blank=True)
    group_name = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=(
            "What the package cost the store when it was bought. The profit "
            "of the order is the price minus this cost."
        ),
    )
    sold_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="What the customer resold this order for, if they did.",
    )
    sold_at = models.DateTimeField(null=True, blank=True)
    buyer_info = models.TextField(
        blank=True,
        help_text="Extra details the buyer typed in the pre-order popup.",
    )
    status = models.CharField(
        max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        help_text="The admin handling this on-demand order.",
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        # The columns the admin filters by and sorts by.
        indexes = [
            models.Index(fields=("product_name",), name="accounts_order_product_idx"),
            models.Index(fields=("package_name",), name="accounts_order_package_idx"),
            models.Index(fields=("status",), name="accounts_order_status_idx"),
            models.Index(fields=("created_at",), name="accounts_order_created_idx"),
            models.Index(fields=("sold_at",), name="accounts_order_sold_idx"),
        ]

    def __str__(self):
        return f"{self.user} - {self.product_name} ({self.package_name})"

    @property
    def is_demand(self):
        """On-demand orders need an admin to work on them."""
        if self.product is not None:
            return self.product.type == "demand"
        return self.status in (
            OrderStatus.PENDING,
            OrderStatus.IN_PROGRESS,
            OrderStatus.HAS_PROBLEMS,
        )

    @property
    def is_instant(self):
        if self.product is not None:
            return self.product.type == "immediate"
        return False

    @property
    def is_sold(self):
        """A sold price means the customer resold this order."""
        return self.sold_price is not None

    @property
    def code_value(self):
        return self.code.code if self.code_id else ""

    @property
    def code_masked(self):
        """Never show a full code in the table — only its first characters."""
        source = self.code_value or self.product_name or ""
        return f"{source[:4].lower()}*****"

    @property
    def code_ready(self):
        return bool(self.code_id and self.code_value)


class OrderReport(models.Model):
    """A problem an admin ran into while handling an on-demand order.

    It is a note: the title and the details the staff wrote down when the
    issue happened. A report is required before an order can move to the
    `has_problems` status, and it stays attached to the order for the history.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="reports"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_reports",
    )
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "order reports"
        # The column the admin filters by and sorts by.
        indexes = [
            models.Index(fields=("created_at",), name="accounts_report_created_idx"),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.title}"


class Notification(models.Model):
    """A message for a user: order updates for customers, new work for admins."""

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    kind = models.CharField(
        max_length=30, choices=NotificationKind.choices, default=NotificationKind.STATUS_CHANGED
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=algeria_now)

    class Meta:
        ordering = ("-created_at", "-id")
        # The columns the admin filters by and sorts by.
        indexes = [
            models.Index(fields=("kind",), name="accounts_notif_kind_idx"),
            models.Index(fields=("is_read",), name="accounts_notif_read_idx"),
            models.Index(fields=("created_at",), name="accounts_notif_created_idx"),
        ]

    def __str__(self):
        return f"{self.recipient}: {self.title}"
