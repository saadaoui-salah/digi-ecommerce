"""The API of the analytics page.

The figures come from the pre-computed tables, so a request never walks the
orders. The daily, monthly and yearly jobs fill those tables.

Every row of those tables belongs to a customer, so a signed-in customer sees
their own figures. Staff can ask for the whole shop with ``?scope=shop``,
which is what the admin dashboard shows.
"""

from decimal import Decimal

from django.db.models import Sum
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product
from apps.core.money import percentage

from .models import AnalyticsPeriod, AnalyticsRun, SalesAggregate
from .serializers import AnalyticsBucketSerializer, AnalyticsProductSerializer
from .services import (
    available_months,
    available_years,
    products_for,
    rows_of,
    series_for,
)

PERIODS = {
    "day": AnalyticsPeriod.DAY,
    "month": AnalyticsPeriod.MONTH,
    "year": AnalyticsPeriod.YEAR,
}


class AnalyticsView(APIView):
    """The figures of the analytics page.

    ``?period=day|month|year`` picks the period, ``?scope=me|shop`` picks
    whose figures are shown (``shop`` is for staff only), ``?month=YYYY-MM``
    keeps the days of one month (with the daily period) and ``?year=YYYY``
    keeps the months of one year (with the monthly period). ``?limit=`` caps
    the number of products of the bar chart.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period_key = request.query_params.get("period", "month")
        period = PERIODS.get(period_key)
        if period is None:
            return Response(
                {"detail": "Unknown period. Use day, month or year."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = request.query_params.get("scope", "me")
        if scope == "shop":
            if not request.user.is_staff:
                return Response(
                    {"detail": "Only staff can see the figures of the shop."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            customer = None
        else:
            scope = "me"
            customer = request.user

        try:
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 50))

        # The daily period can be narrowed down to one month, the monthly
        # period to one year.
        month = request.query_params.get("month") or None
        year = request.query_params.get("year") or None
        if period != AnalyticsPeriod.DAY:
            month = None
        if period != AnalyticsPeriod.MONTH:
            year = None

        products = products_for(period, customer, month, year)[:limit]
        series = series_for(period, customer, month, year)

        total_count = sum(row["count"] for row in series)
        total_spend = sum(Decimal(row["spend"]) for row in series)
        total_benefit = sum(Decimal(row["benefit"]) for row in series)

        cards = self._cards(customer)
        run = AnalyticsRun.objects.filter(period=period).first()

        return Response(
            {
                "period": period_key,
                "scope": scope,
                "month": month,
                "year": year,
                "available_months": available_months(customer),
                "available_years": available_years(customer),
                "updated_at": run.ran_at if run else None,
                "totals": {
                    "count": total_count,
                    "spend": f"{total_spend:.2f}",
                    "benefit": f"{total_benefit:.2f}",
                    "products": rows_of(period, customer, month, year)
                    .values("product_id")
                    .distinct()
                    .count(),
                },
                "cards": cards,
                "products": AnalyticsProductSerializer(
                    products, many=True
                ).data,
                "series": AnalyticsBucketSerializer(series, many=True).data,
            }
        )

    def _cards(self, customer):
        """The headline figures of the page.

        The figures of one customer are the counters of their account. The
        figures of the shop are the counters of the products, so they stay in
        step with the catalog without walking the orders.
        """
        if customer is not None:
            return {
                "net_profit": f"{Decimal(customer.net_profit):.2f}",
                "total_revenue": f"{Decimal(customer.total_revenue):.2f}",
                "net_profit_percentage": f"{Decimal(customer.net_profit_percentage):.2f}",
                "orders_count": customer.orders_count,
                "pending_demand_orders": customer.pending_demand_orders,
                "total_benefit": f"{Decimal(customer.total_benefit):.2f}",
            }

        catalog = Product.objects.aggregate(
            revenue=Sum("total_revenue"),
            profit=Sum("net_profit"),
            benefit=Sum("total_benefit"),
            orders=Sum("sales_count"),
            pending=Sum("pending_demand_orders"),
        )
        return {
            "net_profit": f"{Decimal(catalog['profit'] or 0):.2f}",
            "total_revenue": f"{Decimal(catalog['revenue'] or 0):.2f}",
            "net_profit_percentage": f"{percentage(catalog['profit'], catalog['revenue']):.2f}",
            "orders_count": catalog["orders"] or 0,
            "pending_demand_orders": catalog["pending"] or 0,
            "total_benefit": f"{Decimal(catalog['benefit'] or 0):.2f}",
        }
