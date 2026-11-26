"""The analytics figures: the pre-computed rows and the counters."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Order, OrderStatus
from apps.analytics.models import AnalyticsPeriod, SalesAggregate
from apps.analytics.services import run_daily, run_monthly, run_yearly
from apps.catalog.models import Category, ItemType, Package, PackageCode, Product

User = get_user_model()


def make_order(
    *,
    user,
    product,
    package,
    price="100.00",
    cost="40.00",
    status_value=OrderStatus.DELIVERED,
    sold_price=None,
    days_ago=0,
):
    """An order, placed a number of days ago."""
    from django.utils import timezone

    code = PackageCode.objects.create(
        package=package, code=f"{user.email}-{package.id}-{days_ago}"
    )
    order = Order.objects.create(
        user=user,
        product=product,
        package=package,
        code=code,
        product_name=product.name,
        product_slug=product.slug,
        category_name=product.category.name,
        package_name=package.name,
        price=Decimal(price),
        cost=Decimal(cost),
        status=status_value,
        sold_price=Decimal(sold_price) if sold_price is not None else None,
    )
    if days_ago:
        order.created_at = order.created_at - timezone.timedelta(days=days_ago)
        Order.objects.filter(pk=order.pk).update(created_at=order.created_at)
        order.refresh_from_db()
    return order


class AnalyticsAggregationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bundles", slug="bundles")
        self.product = Product.objects.create(
            category=self.category, name="Pro Pack", slug="pro-pack"
        )
        self.package = Package.objects.create(
            product=self.product,
            name="Monthly",
            price="100.00",
            cost="40.00",
            stock=5,
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit="500.00",
            is_approved=True,
        )

    def test_the_daily_rows_count_the_orders(self):
        make_order(user=self.user, product=self.product, package=self.package)
        make_order(user=self.user, product=self.product, package=self.package)

        run_daily(full=True)

        row = SalesAggregate.objects.get(period=AnalyticsPeriod.DAY)
        self.assertEqual(row.count, 2)
        self.assertEqual(row.spend, Decimal("200.00"))

    def test_the_daily_job_only_touches_the_days_that_changed(self):
        first = make_order(user=self.user, product=self.product, package=self.package)
        run_daily(full=True)

        make_order(user=self.user, product=self.product, package=self.package)
        run_daily()

        total = SalesAggregate.objects.filter(period=AnalyticsPeriod.DAY).aggregate(
            total=Sum("count")
        )
        self.assertEqual(total["total"], 2)
        self.assertTrue(
            SalesAggregate.objects.filter(bucket=first.created_at.date()).exists()
        )

    def test_the_monthly_and_yearly_rows_roll_the_days_up(self):
        make_order(user=self.user, product=self.product, package=self.package)
        make_order(user=self.user, product=self.product, package=self.package, days_ago=40)

        run_daily(full=True)
        run_monthly()
        run_yearly()

        # The two orders are 40 days apart, so they land in two months but
        # in the same year.
        months = SalesAggregate.objects.filter(period=AnalyticsPeriod.MONTH)
        self.assertEqual(months.count(), 2)
        self.assertEqual(sum(month.count for month in months), 2)

        year = SalesAggregate.objects.get(period=AnalyticsPeriod.YEAR)
        self.assertEqual(year.count, 2)

    def test_the_benefit_uses_the_resale_price(self):
        make_order(
            user=self.user,
            product=self.product,
            package=self.package,
            sold_price="150.00",
        )

        run_daily(full=True)

        row = SalesAggregate.objects.get(period=AnalyticsPeriod.DAY)
        self.assertEqual(row.benefit, Decimal("50.00"))


class AnalyticsCountersTests(TestCase):
    """The counters on the customer, the product, the category and the package."""

    def setUp(self):
        self.category = Category.objects.create(name="Bundles", slug="bundles")
        self.product = Product.objects.create(
            category=self.category, name="Pro Pack", slug="pro-pack"
        )
        self.package = Package.objects.create(
            product=self.product,
            name="Monthly",
            price="100.00",
            cost="40.00",
            stock=5,
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit="500.00",
            is_approved=True,
        )

    def test_an_order_moves_every_counter(self):
        make_order(user=self.user, product=self.product, package=self.package)

        self.user.refresh_from_db()
        self.product.refresh_from_db()
        self.category.refresh_from_db()
        self.package.refresh_from_db()

        for target in (self.user, self.product, self.category, self.package):
            self.assertEqual(target.total_revenue, Decimal("100.00"))
            self.assertEqual(target.net_profit, Decimal("60.00"))
            self.assertEqual(target.total_benefit, Decimal("0.00"))

        self.assertEqual(self.user.orders_count, 1)
        self.assertEqual(self.product.sales_count, 1)
        self.assertEqual(self.category.sales_count, 1)
        self.assertEqual(self.package.sales_count, 1)

    def test_a_resale_moves_the_benefit(self):
        order = make_order(
            user=self.user,
            product=self.product,
            package=self.package,
            sold_price="150.00",
        )

        self.user.refresh_from_db()
        self.product.refresh_from_db()
        self.category.refresh_from_db()
        self.package.refresh_from_db()

        for target in (self.user, self.product, self.category, self.package):
            self.assertEqual(target.total_benefit, Decimal("50.00"))
            # The revenue and the profit do not move.
            self.assertEqual(target.total_revenue, Decimal("100.00"))
            self.assertEqual(target.net_profit, Decimal("60.00"))

        order.refresh_from_db()
        self.assertEqual(order.sold_price, Decimal("150.00"))

    def test_a_demand_order_counts_as_pending_until_it_is_delivered(self):
        self.package.type = ItemType.DEMAND
        self.package.save(update_fields=["type"])

        order = make_order(
            user=self.user,
            product=self.product,
            package=self.package,
            status_value=OrderStatus.PENDING,
        )

        self.user.refresh_from_db()
        self.product.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.user.pending_demand_orders, 1)
        self.assertEqual(self.product.pending_demand_orders, 1)
        self.assertEqual(self.category.pending_demand_orders, 1)

        order.status = OrderStatus.DELIVERED
        order.save(update_fields=["status"])

        self.user.refresh_from_db()
        self.product.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.user.pending_demand_orders, 0)
        self.assertEqual(self.product.pending_demand_orders, 0)
        self.assertEqual(self.category.pending_demand_orders, 0)


class AnalyticsApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bundles", slug="bundles")
        self.product = Product.objects.create(
            category=self.category, name="Pro Pack", slug="pro-pack"
        )
        self.package = Package.objects.create(
            product=self.product,
            name="Monthly",
            price="100.00",
            cost="40.00",
            stock=5,
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit="500.00",
            is_approved=True,
        )
        self.staff = User.objects.create_user(
            username="root",
            email="root@example.com",
            password="strong-password-123",
            credit="500.00",
            is_approved=True,
            is_staff=True,
        )

    def _login(self, user):
        """Sign in through the token endpoint — the API reads the JWT cookies."""
        response = self.client.post(
            "/api/auth/token/",
            {"email": user.email, "password": "strong-password-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_page_is_open_to_every_signed_in_customer(self):
        self._login(self.user)

        response = self.client.get("/api/analytics/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scope"], "me")

    def test_a_signed_out_visitor_is_turned_away(self):
        response = self.client.get("/api/analytics/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_customer_sees_their_own_figures(self):
        make_order(user=self.user, product=self.product, package=self.package)
        run_daily(full=True)
        run_monthly()
        self._login(self.user)

        response = self.client.get("/api/analytics/?period=month")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cards"]["orders_count"], 1)
        self.assertEqual(response.data["cards"]["total_revenue"], "100.00")
        self.assertEqual(response.data["cards"]["net_profit"], "60.00")
        self.assertEqual(len(response.data["products"]), 1)
        self.assertEqual(response.data["products"][0]["count"], 1)
        self.assertEqual(response.data["products"][0]["product_name"], "Pro Pack")

    def test_the_daily_period_can_be_narrowed_down_to_one_month(self):
        make_order(user=self.user, product=self.product, package=self.package)
        make_order(user=self.user, product=self.product, package=self.package, days_ago=40)
        run_daily(full=True)
        self._login(self.user)

        response = self.client.get("/api/analytics/?period=day")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["available_months"]), 2)

        month = response.data["available_months"][0]
        narrowed = self.client.get(f"/api/analytics/?period=day&month={month}")

        self.assertEqual(narrowed.status_code, status.HTTP_200_OK)
        self.assertEqual(narrowed.data["month"], month)
        # Every bucket of the narrowed series is inside the chosen month.
        for row in narrowed.data["series"]:
            self.assertTrue(row["bucket"].startswith(month))

    def test_the_monthly_period_can_be_narrowed_down_to_one_year(self):
        make_order(user=self.user, product=self.product, package=self.package)
        run_daily(full=True)
        run_monthly()
        self._login(self.user)

        response = self.client.get("/api/analytics/?period=month")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["available_years"]), 1)

        year = response.data["available_years"][0]
        narrowed = self.client.get(f"/api/analytics/?period=month&year={year}")

        self.assertEqual(narrowed.status_code, status.HTTP_200_OK)
        self.assertEqual(narrowed.data["year"], str(year))
        for row in narrowed.data["series"]:
            self.assertEqual(row["bucket"][:4], str(year))

    def test_a_customer_does_not_see_the_figures_of_the_others(self):
        other = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="strong-password-123",
            credit="500.00",
            is_approved=True,
        )
        make_order(user=other, product=self.product, package=self.package)
        run_daily(full=True)
        run_monthly()
        self._login(self.user)

        response = self.client.get("/api/analytics/?period=month")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["products"], [])
        self.assertEqual(response.data["cards"]["orders_count"], 0)

    def test_the_shop_scope_is_for_staff_only(self):
        self._login(self.user)

        response = self.client.get("/api/analytics/?scope=shop")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_the_staff_see_the_figures_of_the_whole_shop(self):
        make_order(user=self.user, product=self.product, package=self.package)
        run_daily(full=True)
        run_monthly()
        self._login(self.staff)

        response = self.client.get("/api/analytics/?period=month&scope=shop")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scope"], "shop")
        self.assertEqual(response.data["cards"]["orders_count"], 1)
        self.assertEqual(response.data["cards"]["total_revenue"], "100.00")
        self.assertEqual(response.data["cards"]["net_profit"], "60.00")
        self.assertEqual(len(response.data["products"]), 1)
        self.assertEqual(response.data["products"][0]["count"], 1)
        self.assertEqual(response.data["products"][0]["product_name"], "Pro Pack")

    def test_an_unknown_period_is_rejected(self):
        self._login(self.staff)

        response = self.client.get("/api/analytics/?period=century")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_the_net_profit_percentage_follows_the_counters(self):
        make_order(user=self.user, product=self.product, package=self.package)
        self._login(self.user)

        response = self.client.get("/api/analytics/")

        # The price is 100 and the cost is 40, so the margin is 60%.
        self.assertEqual(response.data["cards"]["net_profit_percentage"], "60.00")

        self.user.refresh_from_db()
        self.assertEqual(self.user.net_profit_percentage, Decimal("60.00"))

    def test_the_shop_percentage_is_the_margin_of_the_shop(self):
        make_order(user=self.user, product=self.product, package=self.package)
        self._login(self.staff)

        response = self.client.get("/api/analytics/?scope=shop")

        self.assertEqual(response.data["cards"]["net_profit_percentage"], "60.00")


class AnalyticsAdminPageTests(TestCase):
    """The analytics page of the admin."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="root",
            email="root@example.com",
            password="strong-password-123",
            is_approved=True,
            is_staff=True,
        )

    def test_the_staff_open_the_page(self):
        self.client.force_login(self.staff)

        response = self.client.get("/admin/analytics/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Net profit")
        self.assertContains(response, "Bought products by count")

    def test_a_customer_is_turned_away(self):
        customer = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            is_approved=True,
        )
        self.client.force_login(customer)

        response = self.client.get("/admin/analytics/")

        # The admin site sends anyone who is not staff back to the login.
        self.assertEqual(response.status_code, 302)
