"""Pre-computed sales figures.

The analytics page reads these tables instead of walking the orders on every
request. Three periods are kept side by side:

* ``day``   — one row per product per calendar day
* ``month`` — one row per product per calendar month
* ``year``  — one row per product per calendar year

The daily rows are the base: the monthly and yearly rows are rolled up from
them, so a monthly figure is always the sum of the days it contains.
"""

from django.db import models
from django.utils import timezone

from apps.core.time import now as algeria_now

from apps.accounts.models import User
from apps.catalog.models import Product


class AnalyticsPeriod(models.TextChoices):
    DAY = "day", "Daily"
    MONTH = "month", "Monthly"
    YEAR = "year", "Yearly"


class SalesAggregate(models.Model):
    """How many times a product was bought, and how much was spent on it.

    One row per (user, period, bucket, product). ``bucket`` is the first day
    of the day, the month or the year the figure belongs to, so the rows of a
    month all share the same bucket date and can be summed.

    The rows of one customer are their own analytics; summing them over every
    customer gives the figures of the whole shop.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sales_aggregates",
        help_text="The customer this row belongs to.",
    )
    period = models.CharField(
        max_length=8, choices=AnalyticsPeriod.choices, default=AnalyticsPeriod.DAY
    )
    bucket = models.DateField(
        help_text="First day of the day, month or year this row covers."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="sales_aggregates",
    )
    count = models.PositiveIntegerField(
        default=0, help_text="How many orders bought this product."
    )
    spend = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total price paid for these orders.",
    )
    benefit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=(
            "What the customers resold the orders for, minus what they paid. "
            "Zero while the resale price is unknown."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-bucket", "product__name")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "period", "bucket", "product"),
                name="unique_sales_aggregate_per_user_period_bucket_product",
            )
        ]
        indexes = [
            models.Index(fields=("user", "period", "bucket")),
            models.Index(fields=("period", "product")),
        ]

    def __str__(self):
        return f"{self.get_period_display()} {self.bucket} · {self.product}"

    @property
    def benefit_per_sale(self):
        """The average gain per order, used for the benefit line."""
        if not self.count:
            return 0
        return self.benefit / self.count


class AnalyticsRun(models.Model):
    """When the aggregation jobs last ran, and what they covered.

    The jobs only recompute the buckets that changed, so the log makes it
    obvious what the figures cover and when they were last refreshed.
    """

    period = models.CharField(
        max_length=8, choices=AnalyticsPeriod.choices, unique=True
    )
    last_bucket = models.DateField(
        null=True,
        blank=True,
        help_text="The most recent bucket the job has aggregated.",
    )
    ran_at = models.DateTimeField(default=algeria_now)
    rows = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("period",)

    def __str__(self):
        return f"{self.get_period_display()} · {self.ran_at:%Y-%m-%d %H:%M}"
