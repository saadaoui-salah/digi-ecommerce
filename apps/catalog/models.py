from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Min
from django.utils import timezone
from django.utils.text import slugify

from apps.core.time import now as algeria_now


class ItemType(models.TextChoices):
    DEMAND = "demand", "On demand"
    IMMEDIATE = "immediate", "Immediate"


class SlugModel(models.Model):
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="Auto-generated from the name when left blank.",
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name)[:190] or self._meta.model_name
        slug = base
        number = 2
        while type(self).objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base}-{number}"
            number += 1
        return slug


class Category(SlugModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    image = models.ImageField(upload_to="categories/", blank=True)
    is_active = models.BooleanField(default=True)
    # Counters of what the category sold. The order signals keep them up to
    # date, so the analytics never has to walk the orders.
    sales_count = models.PositiveIntegerField(
        default=0, help_text="How many orders bought a product of this category."
    )
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Everything the customers paid for this category.",
    )
    net_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="The price minus the cost of the packages sold.",
    )
    total_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="What the customers earned by reselling those orders.",
    )
    pending_demand_orders = models.PositiveIntegerField(
        default=0,
        help_text="How many on-demand orders of this category wait to be delivered.",
    )

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "categories"
        # The column the admin searches in and sorts by.
        indexes = [
            models.Index(fields=("name",), name="catalog_category_name_idx"),
        ]

    def __str__(self):
        return self.name


class Product(SlugModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Optional: deleting a category leaves its products in the store.",
    )
    name = models.CharField(max_length=200)
    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True)
    video = models.FileField(
        upload_to="products/videos/",
        blank=True,
        help_text="Short product video (mp4/webm).",
    )
    is_active = models.BooleanField(default=True)
    # Counters of what the product sold. The order signals keep them up to
    # date, so the analytics never has to walk the orders.
    sales_count = models.PositiveIntegerField(
        default=0, help_text="How many orders bought this product."
    )
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Everything the customers paid for this product.",
    )
    net_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="The price minus the cost of the packages sold.",
    )
    total_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="What the customers earned by reselling those orders.",
    )
    pending_demand_orders = models.PositiveIntegerField(
        default=0,
        help_text="How many on-demand orders of this product wait to be delivered.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        # The columns the admin searches in and sorts by.
        indexes = [
            models.Index(fields=("name",), name="catalog_product_name_idx"),
            models.Index(fields=("created_at",), name="catalog_product_created_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def lowest_price(self):
        """The cheapest active package price (for unannotated instances)."""
        return self.packages.filter(is_active=True).aggregate(
            lowest=Min("price")
        )["lowest"]


class Promotion(models.Model):
    """A discount on a product or a whole category.

    The admin fills in either a percentage or a fixed price and the other one
    is calculated from the original price.
    """

    name = models.CharField(max_length=120)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="promotions",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="promotions",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Discount in percent, e.g. 25 for 25% off.",
    )
    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="The price after the discount.",
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "promotions"
        # The columns the admin searches in and sorts by.
        indexes = [
            models.Index(fields=("name",), name="catalog_promotion_name_idx"),
            models.Index(fields=("ends_at",), name="catalog_promotion_ends_idx"),
        ]

    def __str__(self):
        return self.name

    @property
    def base_price(self):
        """The original price the promotion is calculated from."""
        override = getattr(self, "_base_price", None)
        if override is not None:
            return override
        if self.product_id:
            return self.product.lowest_price
        if self.category_id:
            prices = [
                product.lowest_price
                for product in self.category.products.filter(is_active=True)
            ]
            prices = [price for price in prices if price is not None]
            return min(prices) if prices else None
        return None

    @property
    def is_current(self):
        """Active and inside its time window."""
        if not self.is_active:
            return False
        now = algeria_now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True

    @property
    def discount_factor(self):
        """1 - discount, used to price the products down."""
        if self.percentage is not None:
            return max(Decimal("0"), (Decimal("100") - self.percentage) / 100)
        if self.discounted_price is not None and self.base_price:
            factor = self.discounted_price / self.base_price
            return max(Decimal("0"), factor)
        return Decimal("1")

    def price_for(self, price):
        """The discounted price of a given original price."""
        if price is None or not self.is_current:
            return price
        return (Decimal(price) * self.discount_factor).quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        """Keep the percentage and the discounted price in sync."""
        base = self.base_price

        if self.percentage is not None:
            self.percentage = max(Decimal("0"), Decimal(self.percentage))
            if base:
                self.discounted_price = (
                    Decimal(base) * (Decimal("100") - self.percentage) / 100
                ).quantize(Decimal("0.01"))
        elif self.discounted_price is not None and base:
            self.discounted_price = max(Decimal("0"), Decimal(self.discounted_price))
            self.percentage = (
                (Decimal("1") - self.discounted_price / Decimal(base)) * 100
            ).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ImageField(upload_to="products/gallery/")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name_plural = "product images"

    def __str__(self):
        return f"{self.product.name} image {self.sort_order}"


class PackageGroup(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="package_groups"
    )
    name = models.CharField(
        max_length=100, help_text="Country or region, e.g. United States."
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")
        # The column the admin searches in and sorts by.
        indexes = [
            models.Index(fields=("name",), name="catalog_group_name_idx"),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Package(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="packages"
    )
    group = models.ForeignKey(
        PackageGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="packages",
        help_text="Empty for products with a single flat list of packages.",
    )
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=20, choices=ItemType.choices, default=ItemType.IMMEDIATE
    )
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
            "What the admin paid for this package. The profit of a sale is "
            "the price minus this cost."
        ),
    )
    stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Instant packages: how many codes they still hold — the signals "
            "keep it up to date. Demand packages: how many can still be sold."
        ),
    )
    requires_info = models.BooleanField(
        default=False,
        help_text=(
            "Demand packages need the customer to type extra details before "
            "checkout."
        ),
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    # Counters of what the package sold. The order signals keep them up to
    # date, so the analytics never has to walk the orders.
    sales_count = models.PositiveIntegerField(
        default=0, help_text="How many orders bought this package."
    )
    total_revenue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Everything the customers paid for this package.",
    )
    net_profit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="The price minus the cost of this package.",
    )
    total_benefit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="What the customers earned by reselling those orders.",
    )

    class Meta:
        ordering = ("sort_order", "price")
        constraints = [
            models.UniqueConstraint(
                fields=("group", "name"),
                condition=models.Q(group__isnull=False),
                name="catalog_package_unique_name_per_group",
            )
        ]
        # The columns the admin searches in and sorts by.
        indexes = [
            models.Index(fields=("name",), name="catalog_package_name_idx"),
            models.Index(fields=("price",), name="catalog_package_price_idx"),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def is_available(self):
        if not self.is_active:
            return False
        if self.type == ItemType.IMMEDIATE:
            # Instant packages are limited by the codes they hold.
            return self.codes_available > 0
        return self.stock is None or self.stock > 0

    @property
    def codes_available(self):
        """Unused codes for instant packages (uses the `unused_codes` annotation)."""
        annotated = getattr(self, "unused_codes", None)
        if annotated is not None:
            return annotated
        return self.codes.filter(is_used=False).count()

    @property
    def margin(self):
        """What the store earns on one sale of this package."""
        if self.price is None or self.cost is None:
            return Decimal("0")
        return Decimal(self.price) - Decimal(self.cost)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class PackageCode(models.Model):
    """A single deliverable code for an instant package.

    The code is stored as ``email|password``. Packages can hold many codes;
    buying an instant package claims one of them for the customer.
    """

    package = models.ForeignKey(
        Package, on_delete=models.CASCADE, related_name="codes"
    )
    code = models.CharField(
        max_length=255,
        help_text="Credentials in the form email|password. The admin also accepts several space-separated email:password pairs.",
    )
    is_used = models.BooleanField(default=False)
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claimed_package_codes",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name_plural = "package codes"
        # The columns the admin searches in, filters by and sorts by.
        indexes = [
            models.Index(fields=("code",), name="catalog_code_code_idx"),
            models.Index(fields=("is_used",), name="catalog_code_used_idx"),
            models.Index(fields=("claimed_at",), name="catalog_code_claimed_idx"),
            models.Index(fields=("created_at",), name="catalog_code_created_idx"),
        ]

    def __str__(self):
        return f"{self.package.name} - {self.code}"

    @property
    def email(self):
        return self.code.split("|", 1)[0].strip()

    @property
    def password(self):
        parts = self.code.split("|", 1)
        return parts[1].strip() if len(parts) > 1 else ""

    @property
    def is_valid(self):
        return bool(self.email and self.password)
