from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Category,
    ItemType,
    Package,
    PackageCode,
    PackageGroup,
    Product,
    Promotion,
)


class CatalogApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent = Category.objects.create(name="Software", slug="software")
        cls.child = Category.objects.create(
            name="Design Tools", slug="design-tools", parent=cls.parent
        )
        cls.product = Product.objects.create(
            category=cls.child,
            name="Design Suite",
            slug="design-suite",
            short_description="A complete design toolkit.",
            description="Design suite description.",
        )
        cls.package = Package.objects.create(
            product=cls.product,
            name="Monthly",
            price="10.00",
            stock=5,
        )
        # Instant packages are limited by their codes, not by a stock counter.
        PackageCode.objects.create(
            package=cls.package, code="monthly@example.com|monthly-pass"
        )
        cls.out_of_stock = Package.objects.create(
            product=cls.product,
            name="Annual",
            price="50.00",
            stock=0,
            type=ItemType.DEMAND,
        )
        cls.inactive_package = Package.objects.create(
            product=cls.product,
            name="Legacy",
            price="5.00",
            stock=10,
            is_active=False,
        )
        cls.unavailable_product = Product.objects.create(
            category=cls.child,
            name="Sold Out Tool",
            slug="sold-out-tool",
        )
        Package.objects.create(
            product=cls.unavailable_product,
            name="Standard",
            price="20.00",
            stock=0,
        )
        cls.inactive_product = Product.objects.create(
            category=cls.child,
            name="Hidden Tool",
            slug="hidden-tool",
            is_active=False,
        )
        cls.inactive_category = Category.objects.create(
            name="Hidden Category", slug="hidden-category", is_active=False
        )
        cls.demand_product = Product.objects.create(
            category=cls.parent,
            name="Custom Artwork",
            type=ItemType.DEMAND,
        )

    def test_category_browsing(self):
        response = self.client.get("/api/categories/?root=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.parent.id, ids)
        self.assertNotIn(self.child.id, ids)

        response = self.client.get(f"/api/categories/?parent={self.parent.id}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.child.id)

        response = self.client.get("/api/categories/?search=Hidden")
        self.assertEqual(response.data["count"], 0)

    def test_product_search_and_category_filter(self):
        response = self.client.get("/api/products/?search=Design")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.product.id)

        response = self.client.get(
            f"/api/products/?category_slug={self.child.slug}"
        )
        self.assertEqual(response.data["count"], 2)

    def test_product_availability_and_price_filters(self):
        response = self.client.get("/api/products/?available=true")
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.product.id, ids)
        self.assertNotIn(self.unavailable_product.id, ids)
        self.assertNotIn(self.inactive_product.id, ids)

        response = self.client.get("/api/products/?max_price=15")
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.product.id, ids)
        self.assertNotIn(self.unavailable_product.id, ids)

        response = self.client.get("/api/products/?min_price=20")
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(self.product.id, ids)

        response = self.client.get("/api/products/?ordering=price_from")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_product_type_filter(self):
        response = self.client.get("/api/products/?type=demand")
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.demand_product.id, ids)
        self.assertNotIn(self.product.id, ids)

        response = self.client.get("/api/products/?type=immediate")
        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.product.id, ids)
        self.assertNotIn(self.demand_product.id, ids)

    def test_product_detail_includes_active_packages(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        package_ids = [item["id"] for item in response.data["packages"]]
        self.assertIn(self.package.id, package_ids)
        self.assertIn(self.out_of_stock.id, package_ids)
        self.assertNotIn(self.inactive_package.id, package_ids)

        out_of_stock = next(
            item
            for item in response.data["packages"]
            if item["id"] == self.out_of_stock.id
        )
        self.assertFalse(out_of_stock["is_available"])
        # A package always follows the type of its product, and an instant
        # package without codes is not available.
        self.assertEqual(out_of_stock["type"], ItemType.IMMEDIATE)
        self.assertEqual(out_of_stock["codes_available"], 0)

    def test_inactive_category_not_listed(self):
        response = self.client.get("/api/categories/")
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(self.inactive_category.id, ids)

    def test_product_and_category_lookup_by_slug(self):
        response = self.client.get(f"/api/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.product.id)
        self.assertEqual(response.data["category_slug"], self.child.slug)

        response = self.client.get(f"/api/categories/{self.child.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.child.id)

        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/products/does-not-exist/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_grouped_packages_nested_by_country(self):
        group = PackageGroup.objects.create(
            product=self.product, name="United States", sort_order=0
        )
        one_month = Package.objects.create(
            product=self.product,
            group=group,
            name="1 Month",
            price="9.99",
        )
        Package.objects.create(
            product=self.product,
            group=group,
            name="3 Months",
            price="26.99",
            is_active=False,
        )

        response = self.client.get(f"/api/products/{self.product.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        groups = response.data["package_groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["name"], "United States")
        package_ids = [item["id"] for item in groups[0]["packages"]]
        self.assertIn(one_month.id, package_ids)
        self.assertEqual(len(package_ids), 1)

        flat_ids = [item["id"] for item in response.data["packages"]]
        self.assertIn(one_month.id, flat_ids)
        grouped = next(
            item for item in response.data["packages"] if item["id"] == one_month.id
        )
        self.assertEqual(grouped["group"], group.id)


class PromotionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Bundles", slug="bundles")
        cls.product = Product.objects.create(
            category=cls.category, name="Pro Pack", slug="pro-pack"
        )
        Package.objects.create(
            product=cls.product, name="Monthly", price="20.00", stock=3
        )
        cls.other = Product.objects.create(
            category=cls.category, name="Basic Pack", slug="basic-pack"
        )
        Package.objects.create(
            product=cls.other, name="Monthly", price="40.00", stock=3
        )

    def test_percentage_calculates_the_discounted_price(self):
        promotion = Promotion.objects.create(
            name="Spring sale", product=self.product, percentage=Decimal("25.00")
        )

        self.assertEqual(promotion.discounted_price, Decimal("15.00"))

    def test_discounted_price_calculates_the_percentage(self):
        promotion = Promotion.objects.create(
            name="Flash sale",
            product=self.product,
            discounted_price=Decimal("15.00"),
        )

        self.assertEqual(promotion.percentage, Decimal("25.00"))

    def test_product_endpoint_returns_the_discounted_price(self):
        Promotion.objects.create(
            name="Spring sale", product=self.product, percentage=Decimal("50.00")
        )

        response = self.client.get("/api/products/pro-pack/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["price_from"], "20.00")
        self.assertEqual(response.data["price_current"], "10.00")
        self.assertEqual(response.data["promotion"]["percentage"], "50.00")

    def test_category_promotion_applies_to_every_product_in_it(self):
        Promotion.objects.create(
            name="Category sale", category=self.category, percentage=Decimal("10.00")
        )

        response = self.client.get("/api/products/?category_slug=bundles")

        prices = {
            item["slug"]: item["price_current"] for item in response.data["results"]
        }
        self.assertEqual(prices["pro-pack"], "18.00")
        self.assertEqual(prices["basic-pack"], "36.00")

    def test_expired_promotion_is_ignored(self):
        Promotion.objects.create(
            name="Old sale",
            product=self.product,
            percentage=Decimal("50.00"),
            is_active=False,
        )

        response = self.client.get("/api/products/pro-pack/")

        self.assertIsNone(response.data["promotion"])
        self.assertEqual(response.data["price_current"], "20.00")

    def test_package_prices_carry_the_discount(self):
        Promotion.objects.create(
            name="Spring sale", product=self.product, percentage=Decimal("50.00")
        )

        response = self.client.get(f"/api/packages/?product={self.product.id}")

        prices = {item["price_current"] for item in response.data["results"]}
        self.assertEqual(prices, {"10.00"})

    def test_the_promoted_filter_lists_every_promoted_product(self):
        """`promoted=true` returns all promoted products, whatever the category."""
        other_category = Category.objects.create(name="Themes", slug="themes")
        themed = Product.objects.create(
            category=other_category, name="Theme Pack", slug="theme-pack"
        )
        Package.objects.create(
            product=themed, name="Monthly", price="30.00", stock=3
        )
        Promotion.objects.create(
            name="Spring sale", product=self.product, percentage=Decimal("50.00")
        )
        Promotion.objects.create(
            name="Category sale", category=other_category, percentage=Decimal("10.00")
        )

        response = self.client.get("/api/products/?promoted=true")

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"pro-pack", "theme-pack"})

    def test_a_category_filter_lists_the_products_of_that_category(self):
        """A category returns its own products, promoted or not."""
        other_category = Category.objects.create(name="Themes", slug="themes")
        themed = Product.objects.create(
            category=other_category, name="Theme Pack", slug="theme-pack"
        )
        Package.objects.create(
            product=themed, name="Monthly", price="30.00", stock=3
        )
        Promotion.objects.create(
            name="Spring sale", product=self.product, percentage=Decimal("50.00")
        )

        response = self.client.get(f"/api/products/?category={self.category.id}")

        slugs = {item["slug"] for item in response.data["results"]}
        self.assertEqual(slugs, {"pro-pack", "basic-pack"})

    def test_the_product_detail_ships_the_related_products(self):
        """The detail page needs no second request for the siblings."""
        sibling = Product.objects.create(
            category=self.category, name="Extra Pack", slug="extra-pack"
        )
        Package.objects.create(
            product=sibling, name="Monthly", price="15.00", stock=3
        )

        response = self.client.get("/api/products/pro-pack/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        related = {item["slug"] for item in response.data["related"]}
        self.assertIn("extra-pack", related)
        self.assertNotIn("pro-pack", related)


class SlugTests(TestCase):
    def test_slugs_are_generated_and_unique(self):
        category = Category.objects.create(name="Digital Art")
        self.assertEqual(category.slug, "digital-art")

        duplicate = Category.objects.create(name="Digital Art")
        self.assertEqual(duplicate.slug, "digital-art-2")

        product = Product.objects.create(
            category=category, name="Mega Bundle", slug=""
        )
        self.assertEqual(product.slug, "mega-bundle")

class StockTests(TestCase):
    """The stock of a package and the worth of the unsold stock."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user_model = get_user_model()
        self.staff = self.user_model.objects.create_user(
            username="root",
            email="root@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.customer = self.user_model.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            is_approved=True,
        )

        self.category = Category.objects.create(name="Bundles", slug="bundles")
        self.product = Product.objects.create(
            category=self.category, name="Pro Pack", slug="pro-pack"
        )
        self.package = Package.objects.create(
            product=self.product,
            name="Monthly",
            price="100.00",
        )
        self.demand_product = Product.objects.create(
            category=self.category,
            name="On Demand Pack",
            slug="on-demand-pack",
            type=ItemType.DEMAND,
        )
        self.demand_package = Package.objects.create(
            product=self.demand_product,
            name="Annual",
            type=ItemType.DEMAND,
            price="500.00",
            stock=3,
        )

    def test_a_new_code_joins_the_stock(self):
        PackageCode.objects.create(package=self.package, code="a@example.com|pass")

        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 1)

    def test_selling_a_code_leaves_the_stock(self):
        code = PackageCode.objects.create(
            package=self.package, code="a@example.com|pass"
        )
        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 1)

        code.is_used = True
        code.claimed_by = self.customer
        code.save(update_fields=["is_used", "claimed_by"])

        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 0)

    def test_deleting_a_code_leaves_the_stock(self):
        code = PackageCode.objects.create(
            package=self.package, code="a@example.com|pass"
        )
        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 1)

        code.delete()

        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 0)

    def test_the_worth_of_the_unsold_stock_follows_the_codes(self):
        PackageCode.objects.create(package=self.package, code="a@example.com|pass")

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_worth, Decimal("100.00"))

        code = PackageCode.objects.create(
            package=self.package, code="b@example.com|pass"
        )

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_worth, Decimal("200.00"))

        code.is_used = True
        code.claimed_by = self.customer
        code.save(update_fields=["is_used", "claimed_by"])

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_worth, Decimal("100.00"))

    def test_the_quantity_of_the_unsold_stock_follows_the_codes(self):
        PackageCode.objects.create(package=self.package, code="a@example.com|pass")

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_quantity, 1)

        code = PackageCode.objects.create(
            package=self.package, code="b@example.com|pass"
        )

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_quantity, 2)

        code.is_used = True
        code.claimed_by = self.customer
        code.save(update_fields=["is_used", "claimed_by"])

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_quantity, 1)

    def test_a_demand_package_keeps_its_own_stock(self):
        PackageCode.objects.create(
            package=self.demand_package, code="a@example.com|pass"
        )

        self.demand_package.refresh_from_db()
        self.assertEqual(self.demand_package.stock, 3)

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.stock_worth, Decimal("0.00"))

    def test_a_customer_never_carries_the_worth_of_the_shop(self):
        PackageCode.objects.create(package=self.package, code="a@example.com|pass")

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.stock_worth, Decimal("0.00"))

    def test_a_new_staff_account_carries_the_worth_of_the_unsold_stock(self):
        PackageCode.objects.create(package=self.package, code="a@example.com|pass")

        late = self.user_model.objects.create_user(
            username="late",
            email="late@example.com",
            password="strong-password-123",
            is_staff=True,
        )

        self.assertEqual(late.stock_worth, Decimal("100.00"))
        self.assertEqual(late.stock_quantity, 1)


class CategoryDeletionTests(TestCase):
    def test_deleting_a_category_keeps_its_products(self):
        category = Category.objects.create(name="Bundles", slug="bundles")
        product = Product.objects.create(
            name="Temporary Pack", slug="temporary-pack", category=category
        )

        category.delete()
        product.refresh_from_db()

        self.assertIsNone(product.category_id)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
