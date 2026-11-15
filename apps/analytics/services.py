"""Turning the orders into the figures the analytics page shows.

The daily rows are the base: every order lands in the day it was bought. The
monthly and yearly rows are rolled up from them, so a month is always the sum
of the days it contains and the two can never drift apart.

Every row belongs to a customer, so each one sees their own figures. Summing
the rows over all the customers gives the figures of the whole shop, which is
what the admin dashboard shows.

The jobs are incremental. A day is only recomputed when an order in it was
created or resold since the last run, so a daily job stays cheap no matter
how many orders the store has.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Max, Q, Sum
from django.utils import timezone

from apps.accounts.models import Credit, CreditKind, Order, OrderStatus, User
from apps.catalog.models import Product
from apps.core.money import money, percentage

from .charts import bar_chart, line_chart
from .models import AnalyticsPeriod, AnalyticsRun, SalesAggregate

#: Orders that never reach the customer are not a sale.
COUNTED_STATUSES = (
    OrderStatus.PENDING,
    OrderStatus.IN_PROGRESS,
    OrderStatus.HAS_PROBLEMS,
    OrderStatus.DELIVERED,
)

#: How far back the daily job looks for changes by default.
DEFAULT_LOOKBACK_DAYS = 30


def day_bucket(moment) -> date:
    """The day an order belongs to."""
    return _as_date(moment)


def month_bucket(moment) -> date:
    """The first day of the month an order belongs to."""
    return _as_date(moment).replace(day=1)


def year_bucket(moment) -> date:
    """The first day of the year an order belongs to."""
    return _as_date(moment).replace(month=1, day=1)


def _as_date(moment) -> date:
    """A date out of a date or a timestamp, in Algerian time.

    The database stores the Algerian wall clock, so a naive timestamp is
    already the local time and needs no conversion. An aware one is moved
    into the local time first.
    """
    if isinstance(moment, datetime):
        if timezone.is_naive(moment):
            return moment.date()
        return timezone.localtime(moment).date()
    return moment


def _day_start(day: date) -> datetime:
    """The first second of a day, in the same (naive) form as the database."""
    return datetime.combine(day, time.min)


def _benefit_of(order) -> Decimal:
    """What the customer earned by reselling the order."""
    if order.sold_price is None:
        return Decimal("0.00")
    return Decimal(order.sold_price) - Decimal(order.price)


def _profit_of(order) -> Decimal:
    """What the store earned on the order: the price minus what it cost."""
    return Decimal(order.price) - Decimal(order.cost)


def _counted_orders():
    """The orders that count as a sale."""
    return Order.objects.filter(status__in=COUNTED_STATUSES)


def _changed_orders(since=None):
    """The orders that were bought or resold since the given moment."""
    queryset = _counted_orders()
    if since is None:
        return queryset
    return queryset.filter(Q(created_at__gte=since) | Q(sold_at__gte=since))


def _rows_for(buckets: set[date]):
    """The figures of the given day buckets, read from the orders.

    The rows are kept per customer, so each one of them sees their own
    figures.
    """
    if not buckets:
        return {}

    start = _day_start(min(buckets))
    end = _day_start(max(buckets) + timedelta(days=1))

    orders = (
        _counted_orders()
        .filter(created_at__gte=start, created_at__lt=end)
        .select_related("product")
    )

    rows: dict[tuple[int, date, int], list] = {}
    for order in orders.iterator():
        if order.product_id is None:
            continue
        bucket = day_bucket(order.created_at)
        if bucket not in buckets:
            continue
        key = (order.user_id, bucket, order.product_id)
        entry = rows.get(key)
        if entry is None:
            entry = [0, Decimal("0.00"), Decimal("0.00")]
            rows[key] = entry
        entry[0] += 1
        entry[1] += Decimal(order.price)
        entry[2] += _benefit_of(order)

    return rows


def rebuild_days(buckets: set[date]):
    """Recompute the daily rows of the given buckets."""
    if not buckets:
        return 0

    rows = _rows_for(buckets)
    products = {product.pk: product for product in Product.objects.all()}

    SalesAggregate.objects.filter(
        period=AnalyticsPeriod.DAY, bucket__in=buckets
    ).delete()

    aggregates = [
        SalesAggregate(
            user_id=user_id,
            period=AnalyticsPeriod.DAY,
            bucket=bucket,
            product=products[product_id],
            count=count,
            spend=spend,
            benefit=benefit,
        )
        for (user_id, bucket, product_id), (count, spend, benefit) in rows.items()
        if product_id in products
    ]
    SalesAggregate.objects.bulk_create(aggregates, batch_size=500)
    return len(aggregates)


def run_daily(full: bool = False, lookback_days: int = DEFAULT_LOOKBACK_DAYS):
    """Refresh the daily rows.

    Only the days that changed are recomputed. With ``full`` the whole
    history is rebuilt instead.
    """
    if full:
        buckets = {
            day_bucket(created_at)
            for created_at in _counted_orders().values_list("created_at", flat=True)
        }
    else:
        since = timezone.now() - timedelta(days=lookback_days)
        buckets = {
            day_bucket(created_at)
            for created_at in _changed_orders(since).values_list(
                "created_at", flat=True
            )
        }
        # A resale can land on an order from any day in the past, so the days
        # of the resold orders are part of the work as well.
        buckets |= {
            day_bucket(created_at)
            for created_at in _counted_orders()
            .filter(sold_at__gte=since)
            .values_list("created_at", flat=True)
        }

    written = rebuild_days(buckets)
    _record_run(AnalyticsPeriod.DAY, max(buckets) if buckets else None, written)
    return written


def roll_up(period, bucket_of):
    """Rebuild one coarser period from the daily rows.

    ``bucket_of`` turns a day into the bucket of the target period. The rows
    keep their customer, so a month of one customer never mixes with the
    month of another.
    """
    source = SalesAggregate.objects.filter(period=AnalyticsPeriod.DAY).values(
        "user_id", "bucket", "product_id", "count", "spend", "benefit"
    )

    rows: dict[tuple[int, date, int], list] = {}
    for row in source.iterator():
        key = (row["user_id"], bucket_of(row["bucket"]), row["product_id"])
        entry = rows.get(key)
        if entry is None:
            entry = [0, Decimal("0.00"), Decimal("0.00")]
            rows[key] = entry
        entry[0] += row["count"] or 0
        entry[1] += Decimal(row["spend"] or 0)
        entry[2] += Decimal(row["benefit"] or 0)

    SalesAggregate.objects.filter(period=period).delete()

    products = {product.pk: product for product in Product.objects.all()}
    aggregates = [
        SalesAggregate(
            user_id=user_id,
            period=period,
            bucket=bucket,
            product=products[product_id],
            count=count,
            spend=spend,
            benefit=benefit,
        )
        for (user_id, bucket, product_id), (count, spend, benefit) in rows.items()
        if product_id in products
    ]
    SalesAggregate.objects.bulk_create(aggregates, batch_size=500)

    newest = max((key[1] for key in rows), default=None)
    _record_run(period, newest, len(aggregates))
    return len(aggregates)


def run_monthly():
    """Rebuild the monthly rows from the daily ones."""
    return roll_up(AnalyticsPeriod.MONTH, month_bucket)


def run_yearly():
    """Rebuild the yearly rows from the daily ones."""
    return roll_up(AnalyticsPeriod.YEAR, year_bucket)


def _record_run(period, newest_bucket, rows):
    run, _ = AnalyticsRun.objects.get_or_create(period=period)
    run.last_bucket = newest_bucket
    run.ran_at = timezone.now()
    run.rows = rows
    run.save(update_fields=["last_bucket", "ran_at", "rows"])
    return run


def rows_of(period, user=None, month=None, year=None):
    """The rows of a period, for one customer or for the whole shop.

    ``month`` (a ``YYYY-MM`` string) keeps the days of that month, ``year``
    (a number) keeps the buckets of that year.
    """
    queryset = SalesAggregate.objects.filter(period=period)
    if user is not None:
        queryset = queryset.filter(user=user)

    if month:
        parts = str(month).split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            queryset = queryset.filter(
                bucket__year=int(parts[0]), bucket__month=int(parts[1])
            )
    elif year:
        queryset = queryset.filter(bucket__year=int(year))

    return queryset


def available_months(user=None) -> list[str]:
    """The months that hold daily rows, newest first (``YYYY-MM``)."""
    months = {
        row["bucket"].strftime("%Y-%m")
        for row in rows_of(AnalyticsPeriod.DAY, user)
        .values("bucket")
        .distinct()
    }
    return sorted(months, reverse=True)


def available_years(user=None) -> list[int]:
    """The years that hold monthly rows, newest first."""
    years = {
        row["bucket"].year
        for row in rows_of(AnalyticsPeriod.MONTH, user).values("bucket").distinct()
    }
    return sorted(years, reverse=True)


def bucket_label(bucket, period) -> str:
    """The name of a bucket on the axis of the charts.

    It follows the period: a day is "26 Oct", a month is "Oct 2026" and a
    year is "2026". Without it every day of a month would carry the same
    label.
    """
    if period == AnalyticsPeriod.DAY:
        return bucket.strftime("%d %b")
    if period == AnalyticsPeriod.MONTH:
        return bucket.strftime("%b %Y")
    return bucket.strftime("%Y")


def debts_by_region():
    """What the customers of every region owe the shop.

    The free-spend customers pay what they can and owe the rest, so the debt
    of a region is the sum of what its customers still owe.
    """
    rows = (
        Credit.objects.filter(
            kind=CreditKind.DEBT, user__wilaya__isnull=False
        )
        .values("user__wilaya__region__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    return [
        (row["user__wilaya__region__name"], f"{Decimal(row['total'] or 0):.2f}")
        for row in rows
        if row["total"]
    ]


def shop_figures(period=AnalyticsPeriod.MONTH, month=None, year=None):
    """The cards and the charts of the shop.

    The cards read the counters of the catalog rows, so they stay in step with
    the products without walking the orders. The charts read the pre-computed
    rows of the period.
    """
    counters = Product.objects.aggregate(
        revenue=Sum("total_revenue"),
        profit=Sum("net_profit"),
        benefit=Sum("total_benefit"),
        orders=Sum("sales_count"),
        pending=Sum("pending_demand_orders"),
    )

    series = series_for(period, None, month, year)
    products = products_for(period, None, month, year)

    # The worth and the quantity of the unsold stock are figures of the shop,
    # so every staff account carries them — the biggest one is the figure.
    stock = User.objects.filter(is_staff=True).aggregate(
        worth=Max("stock_worth"), quantity=Max("stock_quantity")
    )

    return {
        "cards": {
            "net_profit": money(counters["profit"]),
            "total_revenue": money(counters["revenue"]),
            "net_profit_percentage": f"{percentage(counters['profit'], counters['revenue']):.2f}%",
            "orders_count": counters["orders"] or 0,
            "pending_demand_orders": counters["pending"] or 0,
            "total_benefit": money(counters["benefit"]),
            "stock_worth": money(stock["worth"] or 0),
            "stock_quantity": stock["quantity"] or 0,
        },
        "charts": {
            "products": bar_chart(
                [(item["product"].name, item["count"]) for item in products]
            ),
            "debts": bar_chart(debts_by_region()),
            "spend": line_chart(
                [
                    (bucket_label(row["bucket"], period), row["spend"])
                    for row in series
                ],
                decimals=2,
            ),
            "benefits": line_chart(
                [
                    (bucket_label(row["bucket"], period), row["benefit"])
                    for row in series
                ],
                decimals=2,
            ),
        },
    }


def products_for(period, user=None, month=None, year=None):
    """The figures per product for one period, best sellers first.

    The rows of a period are summed per product, so a product that sold in
    several months of a year is listed once. Without a customer the figures
    of the whole shop are returned.
    """
    rows = (
        rows_of(period, user, month, year)
        .values("product_id")
        .annotate(count=Sum("count"), spend=Sum("spend"), benefit=Sum("benefit"))
        .order_by("-count", "product_id")
    )

    products = {
        product.pk: product
        for product in Product.objects.filter(
            pk__in=[row["product_id"] for row in rows]
        ).select_related("category")
    }

    totals = []
    for row in rows:
        product = products.get(row["product_id"])
        if product is None:
            continue
        totals.append(
            {
                "product": product,
                "count": row["count"] or 0,
                "spend": Decimal(row["spend"] or 0),
                "benefit": Decimal(row["benefit"] or 0),
            }
        )

    totals.sort(key=lambda item: (-item["count"], item["product"].name))
    return totals


def series_for(period, user=None, month=None, year=None):
    """The per-bucket series of one period, oldest first.

    Without a customer the series covers the whole shop.
    """
    rows = (
        rows_of(period, user, month, year)
        .values("bucket")
        .annotate(
            count=Sum("count"),
            spend=Sum("spend"),
            benefit=Sum("benefit"),
        )
        .order_by("bucket")
    )
    return [
        {
            "bucket": row["bucket"],
            "count": row["count"] or 0,
            "spend": f"{Decimal(row['spend'] or 0):.2f}",
            "benefit": f"{Decimal(row['benefit'] or 0):.2f}",
        }
        for row in rows
    ]
