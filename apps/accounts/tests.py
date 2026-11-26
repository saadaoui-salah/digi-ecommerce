from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import (
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
    TransactionKind,
    User,
    Wilaya,
)
from apps.catalog.models import Category, ItemType, Package, PackageCode, Product, Promotion

User = get_user_model()


class AuthApiTests(APITestCase):
    def test_register_signs_in_with_cookies(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "alice@example.com",
                "phone": "+15551234567",
                "first_name": "Alice",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "alice")
        self.assertEqual(response.data["email"], "alice@example.com")
        self.assertEqual(response.data["phone"], "+15551234567")
        self.assertEqual(response.data["credit"], "0.00")
        self.assertIn("access", self.client.cookies)
        self.assertIn("refresh", self.client.cookies)

        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password("strong-password-123"))

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")
        self.assertEqual(response.data["credit"], "0.00")

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "ALICE@example.com",
                "phone": "+15559876543",
                "first_name": "Alice",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("already exists", response.data["email"][0])

    def test_register_rejects_duplicate_phone(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            phone="+15551234567",
            password="strong-password-123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "bob@example.com",
                "phone": "+1 (555) 123-4567",
                "first_name": "Bob",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)
        self.assertIn("already exists", response.data["phone"][0])

    def test_register_normalizes_phone(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "bob@example.com",
                "phone": "+1 (555) 123-4567",
                "first_name": "Bob",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["phone"], "+15551234567")

    def test_register_rejects_invalid_email_and_phone(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "not-an-email",
                "phone": "+15551234567",
                "first_name": "Alice",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "bob@example.com",
                "phone": "123",
                "first_name": "Bob",
                "last_name": "Smith",
                "password": "strong-password-123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_login_by_email_sets_cookies(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
            password="strong-password-123",
        )

        response = self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", response.data)
        self.assertEqual(response.data["user"]["email"], "alice@example.com")
        self.assertIn("access", self.client.cookies)
        self.assertTrue(response.cookies["access"]["httponly"])

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")

    def test_login_with_bad_password(self):
        User.objects.create_user(
            username="alice", email="alice@example.com", password="strong-password-123"
        )
        response = self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorization_header_still_works(self):
        User.objects.create_user(
            username="alice", email="alice@example.com", password="strong-password-123"
        )
        response = self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )
        access = self.client.cookies["access"].value
        self.client.cookies.clear()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")

    def test_refresh_from_cookie(self):
        User.objects.create_user(
            username="alice", email="alice@example.com", password="strong-password-123"
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )
        old_access = self.client.cookies["access"].value

        response = self.client.post("/api/auth/token/refresh/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(self.client.cookies["access"].value, old_access)

    def test_logout_clears_cookies(self):
        User.objects.create_user(
            username="alice", email="alice@example.com", password="strong-password-123"
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.cookies["access"].value, "")

        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def _login(self, email="alice@example.com", password="strong-password-123"):
        User.objects.create_user(
            username="alice",
            email=email,
            phone="+15551234567",
            first_name="Alice",
            last_name="Smith",
            password=password,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": email, "password": password},
            format="json",
        )

    def test_me_update_changes_profile(self):
        self._login()

        response = self.client.patch(
            "/api/auth/me/",
            {
                "first_name": "Alicia",
                "last_name": "Jones",
                "email": "alicia@example.com",
                "phone": "+1 (555) 999-8877",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Alicia")
        self.assertEqual(response.data["email"], "alicia@example.com")
        self.assertEqual(response.data["phone"], "+15559998877")

        user = User.objects.get(username="alice")
        self.assertEqual(user.email, "alicia@example.com")

    def test_me_update_rejects_duplicate_email(self):
        self._login()
        User.objects.create_user(
            username="bob", email="bob@example.com", password="strong-password-123"
        )

        response = self.client.patch(
            "/api/auth/me/",
            {"email": "BOB@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertIn("already exists", response.data["email"][0])

    def test_me_update_rejects_invalid_phone(self):
        self._login()

        response = self.client.patch(
            "/api/auth/me/",
            {"phone": "123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data)

    def test_change_password_updates_credentials(self):
        self._login()

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "strong-password-123",
                "new_password": "even-stronger-password-456",
                "confirm_password": "even-stronger-password-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username="alice")
        self.assertTrue(user.check_password("even-stronger-password-456"))

        response = self.client.post(
            "/api/auth/token/",
            {
                "email": "alice@example.com",
                "password": "even-stronger-password-456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_rejects_wrong_current_password(self):
        self._login()

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "not-the-password",
                "new_password": "even-stronger-password-456",
                "confirm_password": "even-stronger-password-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)

    def test_change_password_rejects_mismatch(self):
        self._login()

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "strong-password-123",
                "new_password": "even-stronger-password-456",
                "confirm_password": "something-else-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    def test_change_password_requires_authentication(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "strong-password-123",
                "new_password": "even-stronger-password-456",
                "confirm_password": "even-stronger-password-456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sub_admin_is_staff(self):
        user = User.objects.create_user(
            username="moderator",
            password="strong-password-123",
            is_sub_admin=True,
        )
        self.assertTrue(user.is_staff)


class TransactionApiTests(APITestCase):
    def _login(self, email="alice@example.com", password="strong-password-123"):
        self.user = User.objects.create_user(
            username="alice",
            email=email,
            phone="+15551234567",
            first_name="Alice",
            last_name="Smith",
            password=password,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": email, "password": password},
            format="json",
        )

    def _login_staff(self):
        staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "staff@example.com", "password": "strong-password-123"},
            format="json",
        )
        return staff

    def test_creating_credit_transaction_increases_balance(self):
        self._login()
        self._login_staff()

        response = self.client.post(
            "/api/auth/transactions/",
            {
                "user": self.user.id,
                "kind": "credit",
                "amount": "2500.00",
                "method": "Bank transfer",
                "note": "Top-up",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["balance_after"], "2500.00")
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("2500.00"))

    def test_creating_an_order_transaction_decreases_balance(self):
        self._login()
        Transaction.objects.create(
            user=self.user, kind="credit", amount=Decimal("1000.00")
        )
        self._login_staff()

        self.client.post(
            "/api/auth/transactions/",
            {"user": self.user.id, "kind": "order", "amount": "400.00"},
            format="json",
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("600.00"))

    def test_transactions_are_listed_for_the_owner(self):
        self._login()
        other = User.objects.create_user(
            username="bob", email="bob@example.com", password="strong-password-123"
        )
        Transaction.objects.create(
            user=self.user, kind="credit", amount=Decimal("100.00")
        )
        Transaction.objects.create(
            user=other, kind="credit", amount=Decimal("900.00")
        )

        response = self.client.get("/api/auth/transactions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["amount"], "100.00")
        self.assertEqual(response.data["results"][0]["amount_signed"], "100.00")

    def test_transaction_summary_reports_totals(self):
        self._login()
        Transaction.objects.create(
            user=self.user, kind="credit", amount=Decimal("1000.00")
        )
        Transaction.objects.create(
            user=self.user, kind="order", amount=Decimal("250.00")
        )

        response = self.client.get("/api/auth/transactions/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_credited"], "1000.00")
        self.assertEqual(response.data["total_debited"], "250.00")
        self.assertEqual(response.data["credit_balance"], "750.00")

    def test_customers_cannot_create_transactions(self):
        self._login()

        response = self.client.post(
            "/api/auth/transactions/",
            {"user": self.user.id, "kind": "credit", "amount": "500.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("0.00"))

    def test_transactions_require_authentication(self):
        response = self.client.get("/api/auth/transactions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_credits_are_listed_for_the_owner(self):
        self._login()
        other = User.objects.create_user(
            username="bob", email="bob@example.com", password="strong-password-123"
        )
        Credit.objects.create(
            user=self.user, kind=CreditKind.TOPUP, amount=Decimal("50.00")
        )
        Credit.objects.create(
            user=self.user, kind=CreditKind.DEBT, amount=Decimal("20.00")
        )
        Credit.objects.create(
            user=other, kind=CreditKind.TOPUP, amount=Decimal("900.00")
        )

        response = self.client.get("/api/auth/credits/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["total_granted"], "50.00")
        self.assertEqual(response.data["total_owed"], "20.00")
        self.assertEqual(response.data["free_spend"], False)
        # The top-up signal already raised the balance by 50.00.
        self.assertEqual(response.data["balance"], "50.00")


class PackageCodeApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Code Gaming", slug="code-gaming"
        )
        self.product = Product.objects.create(
            name="Code Game Pass",
            slug="code-game-pass",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="1 Month",
            type=ItemType.IMMEDIATE,
            price=Decimal("25.00"),
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

    def test_deliver_claims_an_unused_code(self):
        PackageCode.objects.create(
            package=self.package, code="buyer1@example.com|secret-pass"
        )

        response = self.client.post(f"/api/packages/{self.package.id}/deliver/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "buyer1@example.com")
        self.assertEqual(response.data["password"], "secret-pass")

        code = PackageCode.objects.get(package=self.package)
        self.assertTrue(code.is_used)
        self.assertEqual(code.claimed_by, self.user)
        self.assertIsNotNone(code.claimed_at)

    def test_deliver_marks_the_code_as_used(self):
        first = PackageCode.objects.create(
            package=self.package, code="one@example.com|pass-one"
        )
        second = PackageCode.objects.create(
            package=self.package, code="two@example.com|pass-two"
        )

        response = self.client.post(f"/api/packages/{self.package.id}/deliver/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertTrue(first.is_used)
        self.assertFalse(second.is_used)

    def test_deliver_without_codes_returns_conflict(self):
        response = self.client.post(f"/api/packages/{self.package.id}/deliver/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_deliver_requires_authentication(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret"
        )
        self.client.post("/api/auth/logout/", format="json")

        response = self.client.post(f"/api/packages/{self.package.id}/deliver/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_package_detail_reports_available_codes(self):
        PackageCode.objects.create(
            package=self.package, code="one@example.com|pass-one"
        )
        PackageCode.objects.create(
            package=self.package, code="two@example.com|pass-two"
        )

        response = self.client.get("/api/products/code-game-pass/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["packages"][0]["codes_available"], 2)


class OrderApiTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Order Gaming", slug="order-gaming"
        )
        self.product = Product.objects.create(
            name="Order Game Pass",
            slug="order-game-pass",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="1 Month",
            type=ItemType.IMMEDIATE,
            price=Decimal("25.00"),
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit=Decimal("500.00"),
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

    def test_creating_an_instant_order_claims_a_code(self):
        code = PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "delivered")
        self.assertEqual(response.data["code_value"], "buyer@example.com|secret-pass")
        self.assertTrue(response.data["code_ready"])
        self.assertEqual(response.data["code_masked"], "buye*****")

        code.refresh_from_db()
        self.assertTrue(code.is_used)
        self.assertEqual(code.claimed_by, self.user)

        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.code, code)
        self.assertEqual(order.user, self.user)

    def test_creating_an_instant_order_takes_the_code_out_of_the_stock(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 1)

        staff = User.objects.create_user(
            username="root",
            email="root@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.assertEqual(staff.stock_worth, Decimal("25.00"))

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 0)

        # The code left the unsold stock, so the worth of it went down too.
        staff.refresh_from_db()
        self.assertEqual(staff.stock_worth, Decimal("0.00"))
        self.assertEqual(staff.stock_quantity, 0)

    def test_creating_an_order_spends_credit(self):
        self.user.credit = Decimal("100.00")
        self.user.save(update_fields=["credit"])
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("75.00"))
        self.assertTrue(
            self.user.transactions.filter(kind=TransactionKind.ORDER).exists()
        )

    def test_a_promotion_charges_the_discounted_price(self):
        self.user.credit = Decimal("100.00")
        self.user.save(update_fields=["credit"])
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        Promotion.objects.create(
            name="Launch sale", product=self.product, percentage=Decimal("20.00")
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.price, Decimal("20.00"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("80.00"))
        transaction = self.user.transactions.get(kind=TransactionKind.ORDER)
        self.assertEqual(transaction.amount, Decimal("20.00"))

    def test_creating_an_order_without_credit_fails(self):
        self.user.credit = Decimal("0.00")
        self.user.save(update_fields=["credit"])
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_a_free_spend_user_can_buy_with_zero_credit(self):
        """Free spend buys on an empty balance and records what is owed."""
        self.user.credit = Decimal("0.00")
        self.user.free_spend = True
        self.user.save(update_fields=["credit", "free_spend"])
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.user.refresh_from_db()
        # The balance never reads negative — the shortfall lives on Credit.
        self.assertEqual(self.user.credit, Decimal("0.00"))
        self.assertFalse(
            Transaction.objects.filter(user=self.user, kind=TransactionKind.ORDER).exists()
        )
        debt = Credit.objects.get(user=self.user, kind=CreditKind.DEBT)
        self.assertEqual(debt.amount, Decimal("25.00"))
        self.assertEqual(debt.order_id, response.data["id"])

    def test_a_free_spend_user_pays_the_balance_they_have(self):
        """Only the shortfall is credited; the rest is charged as usual."""
        self.user.credit = Decimal("10.00")
        self.user.free_spend = True
        self.user.save(update_fields=["credit", "free_spend"])
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("0.00"))
        charge = Transaction.objects.get(user=self.user, kind=TransactionKind.ORDER)
        self.assertEqual(charge.amount, Decimal("10.00"))
        debt = Credit.objects.get(user=self.user, kind=CreditKind.DEBT)
        self.assertEqual(debt.amount, Decimal("15.00"))

    def test_an_unflagged_user_still_bottoms_out_at_zero(self):
        """Without the flag a purchase can never push the balance below zero."""
        self.user.credit = Decimal("10.00")
        self.user.save(update_fields=["credit"])
        Transaction.objects.create(
            user=self.user, kind=TransactionKind.ORDER, amount=Decimal("999.00")
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("0.00"))

    def test_an_admin_topup_credit_increases_the_balance(self):
        """Saving a top-up in the admin adds the amount — a debt row does not."""
        self.user.credit = Decimal("5.00")
        self.user.save(update_fields=["credit"])

        Credit.objects.create(
            user=self.user, kind=CreditKind.TOPUP, amount=Decimal("40.00")
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("45.00"))

        Credit.objects.create(
            user=self.user, kind=CreditKind.DEBT, amount=Decimal("100.00")
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.credit, Decimal("45.00"))

    def test_an_admin_topup_notifies_the_customer(self):
        """A granted top-up reaches the customer's notification list."""
        Credit.objects.create(
            user=self.user, kind=CreditKind.TOPUP, amount=Decimal("40.00")
        )

        response = self.client.get("/api/auth/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kinds = [item["kind"] for item in response.data["results"]]
        self.assertIn(NotificationKind.CREDIT_TOPUP, kinds)
        notification = next(
            item
            for item in response.data["results"]
            if item["kind"] == NotificationKind.CREDIT_TOPUP
        )
        self.assertIn("40.00", notification["body"])

    def test_a_debt_row_does_not_notify_the_customer(self):
        """Free-spend purchases stay quiet — only granted credits speak up."""
        Credit.objects.create(
            user=self.user, kind=CreditKind.DEBT, amount=Decimal("100.00")
        )

        response = self.client.get("/api/auth/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        kinds = [item["kind"] for item in response.data["results"]]
        self.assertNotIn(NotificationKind.CREDIT_TOPUP, kinds)

    def test_orders_are_listed_for_the_owner(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        response = self.client.get("/api/auth/orders/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_name"], "Order Game Pass")

    def test_order_summary_reports_totals(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        response = self.client.get("/api/auth/orders/summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_orders"], 1)
        self.assertEqual(response.data["total_spent"], "25.00")
        self.assertEqual(response.data["total_sold"], "0.00")
        self.assertEqual(response.data["sold_count"], 0)

    def test_owner_can_record_a_sold_price(self):
        code = PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()

        response = self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "40.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sold_price"], "40.00")
        self.assertTrue(response.data["is_sold"])

        order.refresh_from_db()
        self.assertEqual(order.sold_price, Decimal("40.00"))
        self.assertIsNotNone(order.sold_at)
        self.assertEqual(order.code, code)

    def test_a_sold_price_can_be_cleared(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()
        self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "40.00"},
            format="json",
        )

        response = self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["sold_price"])
        order.refresh_from_db()
        self.assertIsNone(order.sold_at)

    def test_negative_sold_price_is_rejected(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()

        response = self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "-5.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_another_customers_order_cannot_be_marked_sold(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()
        stranger = User.objects.create_user(
            username="mallory",
            email="mallory@example.com",
            password="strong-password-123",
        )

        client = APIClient()
        client.force_authenticate(stranger)

        response = client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "40.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_orders_can_be_searched(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        response = self.client.get("/api/auth/orders/?search=game")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        empty = self.client.get("/api/auth/orders/?search=nothing-here")
        self.assertEqual(empty.data["count"], 0)

    def test_orders_filter_by_sold(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()
        self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "40.00"},
            format="json",
        )

        sold = self.client.get("/api/auth/orders/?sold=true")
        unsold = self.client.get("/api/auth/orders/?sold=false")

        self.assertEqual(sold.data["count"], 1)
        self.assertEqual(sold.data["results"][0]["sold_price"], "40.00")
        self.assertEqual(unsold.data["count"], 0)

    def test_order_summary_counts_sales(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        order = Order.objects.get()
        self.client.patch(
            f"/api/auth/orders/{order.pk}/sold/",
            {"sold_price": "40.00"},
            format="json",
        )

        response = self.client.get("/api/auth/orders/summary/")

        self.assertEqual(response.data["total_sold"], "40.00")
        self.assertEqual(response.data["sold_count"], 1)

    def test_orders_require_authentication(self):
        self.client.post("/api/auth/logout/", format="json")

        response = self.client.get("/api/auth/orders/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ApprovalApiTests(APITestCase):
    def test_new_accounts_start_unapproved(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "newbie@example.com",
                "phone": "+15550001111",
                "first_name": "New",
                "last_name": "Bie",
                "password": "strong-password-123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["is_approved"])
        self.assertFalse(User.objects.get(email="newbie@example.com").is_approved)

    def test_me_reports_the_approval_state(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            is_approved=True,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_approved"])

    def test_staff_can_approve_an_account(self):
        account = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
        )
        staff = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "staff@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.post(
            f"/api/auth/users/{account.id}/approval/",
            {"action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_approved"])
        account.refresh_from_db()
        self.assertTrue(account.is_approved)
        self.assertIsNotNone(account.approved_at)
        self.assertEqual(staff.email, "staff@example.com")

        notification = account.notifications.get()
        self.assertEqual(notification.kind, NotificationKind.ACCOUNT_APPROVED)
        self.assertFalse(notification.is_read)

    def test_revoking_approval_does_not_notify(self):
        account = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            is_approved=True,
        )
        User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "staff@example.com", "password": "strong-password-123"},
            format="json",
        )

        self.client.post(
            f"/api/auth/users/{account.id}/approval/",
            {"action": "revoke"},
            format="json",
        )

        self.assertEqual(account.notifications.count(), 0)

    def test_customers_cannot_approve_accounts(self):
        account = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.post(
            f"/api/auth/users/{account.id}/approval/",
            {"action": "approve"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        account.refresh_from_db()
        self.assertFalse(account.is_approved)


class OnDemandWorkflowTests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Demand Gaming", slug="demand-gaming"
        )
        self.product = Product.objects.create(
            name="Custom Artwork",
            slug="custom-artwork-demand",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="Full custom work",
            type=ItemType.DEMAND,
            price=Decimal("120.00"),
        )
        self.customer = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit=Decimal("500.00"),
            is_approved=True,
        )
        self.admin = User.objects.create_user(
            username="admin-one",
            email="admin@example.com",
            password="strong-password-123",
            is_staff=True,
        )
        self.admin_two = User.objects.create_user(
            username="admin-two",
            email="admin2@example.com",
            password="strong-password-123",
            is_staff=True,
        )

    def _place_order(self):
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )
        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Order.objects.get(pk=response.data["id"])

    def _login_admin(self, email="admin@example.com"):
        self.client.post(
            "/api/auth/token/",
            {"email": email, "password": "strong-password-123"},
            format="json",
        )

    def test_a_product_can_require_buyer_info(self):
        self.package.requires_info = True
        self.package.save(update_fields=["requires_info"])
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("buyer_info", response.data)
        self.assertEqual(Order.objects.count(), 0)

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id, "buyer_info": "My username: alice123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.buyer_info, "My username: alice123")

    def test_an_instant_product_ignores_the_info_flag(self):
        """The popup only applies to on-demand products."""
        instant_product = Product.objects.create(
            name="Instant Top-up",
            slug="instant-topup-demand-test",
            category=self.category,
        )
        instant_package = Package.objects.create(
            product=instant_product,
            name="100 Coins",
            type=ItemType.IMMEDIATE,
            price=Decimal("10.00"),
        )
        PackageCode.objects.create(
            package=instant_package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": instant_package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_demand_order_is_pending_and_notifies_the_admins(self):
        order = self._place_order()

        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertIsNone(order.assigned_to)

        for admin in (self.admin, self.admin_two):
            self.assertTrue(
                Notification.objects.filter(
                    recipient=admin, order=order, kind=NotificationKind.ORDER_PLACED
                ).exists()
            )

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.customer, order=order
            ).exists()
        )

    def test_admin_takes_the_order_and_the_customer_is_notified(self):
        order = self._place_order()
        self._login_admin()

        response = self.client.post(f"/api/auth/orders/{order.pk}/take/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.assigned_to, self.admin)
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.customer,
                order=order,
                kind=NotificationKind.ORDER_ASSIGNED,
            ).exists()
        )
        # The other admin no longer has an open task for this order.
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.admin_two,
                order=order,
                kind=NotificationKind.ORDER_PLACED,
                is_read=False,
            ).exists()
        )

    def test_an_order_can_only_be_taken_once(self):
        order = self._place_order()
        self._login_admin()
        self.client.post(f"/api/auth/orders/{order.pk}/take/")

        self.client.post(
            "/api/auth/token/",
            {"email": "admin2@example.com", "password": "strong-password-123"},
            format="json",
        )
        response = self.client.post(f"/api/auth/orders/{order.pk}/take/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_status_change_notifies_the_customer(self):
        order = self._place_order()
        self._login_admin()

        response = self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {"status": OrderStatus.IN_PROGRESS},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.customer,
                order=order,
                kind=NotificationKind.STATUS_CHANGED,
            ).exists()
        )

    def test_problems_require_a_report(self):
        order = self._place_order()
        self._login_admin()

        response = self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {"status": OrderStatus.HAS_PROBLEMS},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_problems_with_a_report_are_stored(self):
        order = self._place_order()
        self._login_admin()

        response = self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {
                "status": OrderStatus.HAS_PROBLEMS,
                "report": {
                    "title": "Missing reference files",
                    "details": "The customer did not send the logo.",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, OrderStatus.HAS_PROBLEMS)
        report = order.reports.get()
        self.assertEqual(report.title, "Missing reference files")
        self.assertEqual(report.author, self.admin)

    def test_delivering_keeps_the_reports_on_the_order(self):
        order = self._place_order()
        self._login_admin()
        self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {
                "status": OrderStatus.HAS_PROBLEMS,
                "report": {"title": "Missing reference files"},
            },
            format="json",
        )

        response = self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {"status": OrderStatus.DELIVERED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The report is a note: it stays with the order for the history.
        report = order.reports.get()
        self.assertEqual(report.title, "Missing reference files")

    def test_customers_cannot_change_the_status(self):
        order = self._place_order()

        response = self.client.post(
            f"/api/auth/orders/{order.pk}/status/",
            {"status": OrderStatus.DELIVERED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_reads_the_notifications(self):
        order = self._place_order()
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.get("/api/auth/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["count"] >= 1)
        self.assertEqual(response.data["results"][0]["order_id"], order.pk)

    def test_notifications_can_be_marked_as_read(self):
        self._place_order()
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

        response = self.client.post("/api/auth/notifications/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.customer, is_read=False
            ).exists()
        )


class AdminTests(APITestCase):
    def test_on_demand_processing_page_renders(self):
        staff = User.objects.create_user(
            username="staffer",
            email="staffer@example.com",
            password="admin-password",
            is_staff=True,
        )
        category = Category.objects.create(name="Demand", slug="demand-board")
        product = Product.objects.create(
            name="Custom Work",
            slug="custom-work-board",
            category=category,
        )
        package = Package.objects.create(
            product=product,
            name="Full",
            price=Decimal("50.00"),
        )
        customer = User.objects.create_user(
            username="alice", email="alice@example.com", password="admin-password"
        )
        Order.objects.create(
            user=customer,
            product=product,
            package=package,
            product_name=product.name,
            package_name=package.name,
            price=package.price,
            status=OrderStatus.PENDING,
        )

        client = Client()
        client.force_login(staff)

        response = client.get("/admin/accounts/order/processing/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "On-demand orders")
        self.assertContains(response, "Update status")
        self.assertContains(response, "Take this order")

    def test_admin_can_take_an_order_from_the_processing_page(self):
        staff = User.objects.create_user(
            username="staffer",
            email="staffer@example.com",
            password="admin-password",
            is_staff=True,
        )
        category = Category.objects.create(name="Demand", slug="demand-admin")
        product = Product.objects.create(
            name="Custom Work",
            slug="custom-work-admin",
            category=category,
        )
        package = Package.objects.create(
            product=product,
            name="Full",
            price=Decimal("50.00"),
        )
        customer = User.objects.create_user(
            username="alice", email="alice@example.com", password="admin-password"
        )
        order = Order.objects.create(
            user=customer,
            product=product,
            package=package,
            product_name=product.name,
            package_name=package.name,
            price=package.price,
            status=OrderStatus.PENDING,
        )

        client = Client()
        client.force_login(staff)
        response = client.post(
            "/admin/accounts/order/processing/",
            {"order_id": order.pk, "action": "take"},
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.assigned_to, staff)
        self.assertEqual(order.status, OrderStatus.IN_PROGRESS)

    def test_unfold_dashboard_renders(self):
        User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin-password"
        )
        client = Client()
        client.login(username="admin", password="admin-password")

        response = client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Customers")
        self.assertContains(response, "Packages")
        self.assertEqual(client.get("/admin/accounts/user/add/").status_code, 200)
        self.assertEqual(client.get("/admin/catalog/product/").status_code, 200)
        self.assertEqual(client.get("/admin/catalog/product/add/").status_code, 200)


class CouponTests(APITestCase):
    """The coupons of the customers."""

    def setUp(self):
        self.category = Category.objects.create(name="Coupons", slug="coupons")
        self.product = Product.objects.create(
            name="Coupon Game Pass",
            slug="coupon-game-pass",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="1 Month",
            type=ItemType.IMMEDIATE,
            price=Decimal("100.00"),
        )
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="strong-password-123",
            credit=Decimal("500.00"),
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "alice@example.com", "password": "strong-password-123"},
            format="json",
        )

    def test_the_code_is_generated_and_the_other_price_filled_in(self):
        coupon = Coupon.objects.create(
            user=self.user,
            product=self.product,
            percentage=Decimal("10.00"),
        )

        self.assertTrue(coupon.code.startswith("DIGI"))
        # Ten percent off the hundred of the package.
        self.assertEqual(coupon.discount_price, Decimal("90.00"))

    def test_a_discounted_price_gives_the_percentage(self):
        coupon = Coupon.objects.create(
            user=self.user,
            product=self.product,
            discount_price=Decimal("75.00"),
        )

        self.assertEqual(coupon.percentage, Decimal("25.00"))

    def test_the_coupon_is_shown_on_the_page_of_the_product(self):
        Coupon.objects.create(
            user=self.user,
            product=self.product,
            percentage=Decimal("10.00"),
            max_orders=3,
        )

        response = self.client.get(f"/api/products/{self.product.slug}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["coupon"])
        self.assertEqual(response.data["coupon"]["price"], "100.00")
        self.assertEqual(response.data["coupon"]["discount_price_of"], "90.00")
        self.assertEqual(response.data["coupon"]["remaining_orders"], 3)

    def test_the_coupon_brings_the_price_down(self):
        Coupon.objects.create(
            user=self.user,
            product=self.product,
            percentage=Decimal("10.00"),
        )
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(order.price, Decimal("90.00"))

    def test_the_coupon_is_used_up_after_its_orders(self):
        coupon = Coupon.objects.create(
            user=self.user,
            product=self.product,
            percentage=Decimal("10.00"),
            max_orders=1,
        )
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )

        self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        coupon.refresh_from_db()
        self.assertEqual(coupon.used_orders, 1)
        self.assertFalse(coupon.is_active)


class ReferralTests(APITestCase):
    """The referral program."""

    def setUp(self):
        self.category = Category.objects.create(
            name="Referrals", slug="referrals"
        )
        self.product = Product.objects.create(
            name="Referral Game Pass",
            slug="referral-game-pass",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="1 Month",
            type=ItemType.IMMEDIATE,
            price=Decimal("100.00"),
        )
        self.referrer = User.objects.create_user(
            username="referrer",
            email="referrer@example.com",
            password="strong-password-123",
            credit=Decimal("0.00"),
            accepts_referrals=True,
            referral_percentage=Decimal("10.00"),
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="strong-password-123",
            credit=Decimal("500.00"),
        )

    def _buy(self):
        PackageCode.objects.create(
            package=self.package, code="buyer@example.com|secret-pass"
        )
        self.client.post(
            "/api/auth/token/",
            {"email": "buyer@example.com", "password": "strong-password-123"},
            format="json",
        )
        response = self.client.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Order.objects.get(pk=response.data["id"])

    def test_an_account_opened_with_a_referral_code_keeps_the_referrer(self):
        self.referrer.referral_code = "REF1234"
        self.referrer.save(update_fields=["referral_code"])

        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new@example.com",
                "phone": "+213555000001",
                "first_name": "New",
                "last_name": "Customer",
                "password": "strong-password-123",
                "referral_code": "REF1234",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account = User.objects.get(email="new@example.com")
        self.assertEqual(account.referred_by, self.referrer)

    def test_a_referred_order_pays_the_referrer(self):
        self.buyer.referred_by = self.referrer
        self.buyer.save(update_fields=["referred_by"])

        order = self._buy()

        self.referrer.refresh_from_db()
        # Ten percent of the hundred of the order.
        self.assertEqual(self.referrer.credit, Decimal("10.00"))

        referral = Referral.objects.get()
        self.assertEqual(referral.referrer, self.referrer)
        self.assertEqual(referral.referred, self.buyer)
        self.assertEqual(referral.amount, Decimal("10.00"))
        self.assertEqual(referral.order, order)

    def test_the_earning_is_recorded_with_its_own_type(self):
        self.buyer.referred_by = self.referrer
        self.buyer.save(update_fields=["referred_by"])

        self._buy()

        transaction = Transaction.objects.get(
            user=self.referrer, kind=TransactionKind.REFERRAL
        )
        self.assertEqual(transaction.amount, Decimal("10.00"))

        credit = Credit.objects.get(user=self.referrer, kind=CreditKind.REFERRAL)
        self.assertEqual(credit.amount, Decimal("10.00"))

    def test_the_earning_pays_the_debt_first(self):
        Credit.objects.create(
            user=self.referrer,
            kind=CreditKind.DEBT,
            amount=Decimal("4.00"),
            note="Free spend",
        )
        self.buyer.referred_by = self.referrer
        self.buyer.save(update_fields=["referred_by"])

        self._buy()

        self.referrer.refresh_from_db()
        # Four of the ten went to the debt, the rest to the balance.
        self.assertEqual(self.referrer.credit, Decimal("6.00"))
        self.assertFalse(
            Credit.objects.filter(user=self.referrer, kind=CreditKind.DEBT).exists()
        )

    def test_the_program_shows_the_link_and_the_earnings(self):
        self.buyer.referred_by = self.referrer
        self.buyer.save(update_fields=["referred_by"])
        self._buy()

        self.client.post(
            "/api/auth/token/",
            {"email": "referrer@example.com", "password": "strong-password-123"},
            format="json",
        )
        response = self.client.get("/api/auth/referrals/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], self.referrer.referral_code)
        self.assertEqual(response.data["total_earned"], "10.00")
        self.assertEqual(response.data["referred_count"], 1)
        self.assertEqual(response.data["earnings"][0]["referred_email"], "buyer@example.com")

    def test_a_customer_without_the_box_earns_nothing(self):
        self.referrer.accepts_referrals = False
        self.referrer.save(update_fields=["accepts_referrals"])
        self.buyer.referred_by = self.referrer
        self.buyer.save(update_fields=["referred_by"])

        self._buy()

        self.referrer.refresh_from_db()
        self.assertEqual(self.referrer.credit, Decimal("0.00"))
        self.assertFalse(Referral.objects.exists())


class RegionTests(APITestCase):
    """The public wilaya and daira pickers; regions stay admin-only."""

    def setUp(self):
        self.region = Region.objects.create(name="Centre")
        self.wilaya = Wilaya.objects.create(name="Alger", region=self.region)
        self.daira = Daira.objects.create(
            name="Bab El Oued", wilaya=self.wilaya
        )
        self.other_daira = Daira.objects.create(
            name="Blida", wilaya=Wilaya.objects.create(name="Blida", region=self.region)
        )

    def _register(self, **extra):
        payload = {
            "email": "new@example.com",
            "phone": "+213555000002",
            "first_name": "New",
            "last_name": "Customer",
            "password": "strong-password-123",
        }
        payload.update(extra)
        return self.client.post("/api/auth/register/", payload, format="json")

    def test_the_public_api_lists_wilayas_without_regions(self):
        response = self.client.get("/api/auth/wilayas/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [wilaya["name"] for wilaya in response.data]
        self.assertIn("Alger", names)
        self.assertIn("Blida", names)
        self.assertNotIn("region", response.data[0])
        self.assertNotIn("dairas", response.data[0])

    def test_the_dairas_are_fetched_for_one_wilaya(self):
        response = self.client.get(
            f"/api/auth/dairas/?wilaya={self.wilaya.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [daira["name"] for daira in response.data]
        self.assertIn("Bab El Oued", names)
        self.assertNotIn("Blida", names)

    def test_the_daira_endpoint_requires_a_wilaya(self):
        response = self.client.get("/api/auth/dairas/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_an_account_can_pick_a_wilaya_and_a_daira(self):
        response = self._register(
            wilaya=self.wilaya.id, daira=self.daira.id
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account = User.objects.get(email="new@example.com")
        self.assertEqual(account.wilaya, self.wilaya)
        self.assertEqual(account.daira, self.daira)

    def test_the_daira_has_to_be_in_the_wilaya(self):
        response = self._register(
            wilaya=self.wilaya.id, daira=self.other_daira.id
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("daira", response.data)


class ConcurrentCodeTests(APITestCase):
    """Two customers never receive the same code."""

    def setUp(self):
        self.category = Category.objects.create(name="Race", slug="race")
        self.product = Product.objects.create(
            name="Race Pass",
            slug="race-pass",
            category=self.category,
        )
        self.package = Package.objects.create(
            product=self.product,
            name="1 Month",
            type=ItemType.IMMEDIATE,
            price=Decimal("10.00"),
        )
        self.code = PackageCode.objects.create(
            package=self.package, code="only@example.com|secret-pass"
        )

    def _client_for(self, email):
        User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password="strong-password-123",
            credit=Decimal("100.00"),
        )
        client = APIClient()
        response = client.post(
            "/api/auth/token/",
            {"email": email, "password": "strong-password-123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return client

    def test_two_customers_cannot_claim_the_same_code(self):
        first = self._client_for("first@example.com")
        second = self._client_for("second@example.com")

        ok = first.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        denied = second.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.assertEqual(ok.status_code, status.HTTP_201_CREATED)
        # In this sequential test the serializer sees the empty package first
        # (400). Under a true race both requests pass validation and the
        # conditional UPDATE is the one that decides (409).
        self.assertIn(
            denied.status_code,
            (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
        )

        self.code.refresh_from_db()
        self.assertTrue(self.code.is_used)
        self.assertEqual(self.code.order.user.email, "first@example.com")
        # The order of the second customer did not take the code.
        self.assertEqual(Order.objects.count(), 1)

    def test_the_stock_moves_once_for_the_code(self):
        first = self._client_for("first@example.com")
        second = self._client_for("second@example.com")

        first.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )
        second.post(
            "/api/auth/orders/",
            {"package": self.package.id},
            format="json",
        )

        self.package.refresh_from_db()
        self.assertEqual(self.package.stock, 0)
        self.assertEqual(self.package.codes_available, 0)


class WilayaStringTests(APITestCase):
    def test_an_ungrouped_wilaya_renders_its_name(self):
        wilaya = Wilaya.objects.create(name="Alger")

        self.assertEqual(str(wilaya), "Alger")

    def test_a_grouped_wilaya_renders_its_name_and_region(self):
        region = Region.objects.create(name="Centre")
        wilaya = Wilaya.objects.create(name="Alger", region=region)

        self.assertEqual(str(wilaya), "Alger — Centre")


class AdminUiTests(APITestCase):
    def test_approval_fields_live_in_personal_info(self):
        from apps.accounts.admin import UserAdmin

        fieldsets = dict(UserAdmin.fieldsets)
        personal = fieldsets["Personal info"]["fields"]

        self.assertIn("is_approved", personal)
        self.assertIn("approved_at", personal)
        self.assertNotIn("Approval", fieldsets)

    def test_admin_change_lists_include_the_row_click_script(self):
        admin_user = User.objects.create_superuser(
            username="admin-ui", email="admin-ui@example.com", password="pass"
        )
        self.client.force_login(admin_user)

        response = self.client.get("/admin/accounts/user/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "window.location.assign(link.href)")
