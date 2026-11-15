"""Create demo orders so the customer history is not empty.

Instant orders claim a real code, on-demand orders stay without one until
staff attaches it. A debit transaction is recorded for each purchase, exactly
like a real checkout.

    python manage.py seed_orders
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import Order, OrderStatus, Transaction, TransactionKind
from apps.catalog.models import ItemType, Package, PackageCode
from apps.core.time import now as algeria_now

User = get_user_model()

DEMO_ORDERS = [
    # (product slug, package name, group name, status, attach a code)
    ("automation-workflow-library", None, None, OrderStatus.DELIVERED, True),
    ("game-pass", "1 Month", "United States", OrderStatus.DELIVERED, True),
    ("ai-image-prompt-pack", None, None, OrderStatus.DELIVERED, True),
    ("notion-dashboard-template", None, None, OrderStatus.PENDING, False),
    ("landing-page-sprint", None, None, OrderStatus.PENDING, False),
]


class Command(BaseCommand):
    help = "Create demo orders linked to package codes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Only seed this customer (defaults to every customer).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing demo orders (and their transactions) first.",
        )

    def handle(self, *args, **options):
        from apps.catalog.models import Product

        users = User.objects.filter(is_superuser=False)
        if options.get("email"):
            users = users.filter(email__iexact=options["email"])

        if options.get("reset"):
            Order.objects.all().delete()
            Transaction.objects.filter(
                kind__in=(TransactionKind.ORDER, "debit")
            ).delete()
            # Recompute the balances from the movements that are left.
            for account in User.objects.filter(is_superuser=False):
                balance = sum(
                    (item.signed_amount for item in account.transactions.all()),
                    Decimal("0.00"),
                )
                account.credit = max(Decimal("0.00"), balance)
                account.save(update_fields=["credit"])
            self.stdout.write(self.style.WARNING("Removed existing demo orders."))

        created = 0
        for user in users:
            if user.orders.exists():
                continue
            for index, (slug, package_name, group_name, status, attach) in enumerate(
                DEMO_ORDERS
            ):
                product = Product.objects.filter(slug=slug).first()
                if product is None:
                    continue

                package = None
                candidates = Package.objects.filter(product=product)
                if group_name:
                    candidates = candidates.filter(group__name=group_name)
                if package_name:
                    candidates = candidates.filter(name=package_name)
                package = candidates.order_by("price").first()
                if package is None:
                    continue

                group = package.group

                code = None
                if attach:
                    code = (
                        PackageCode.objects.filter(
                            package=package, is_used=False
                        )
                        .order_by("created_at", "id")
                        .first()
                    )
                    if code is not None:
                        code.is_used = True
                        code.claimed_by = user
                        code.claimed_at = algeria_now()
                        code.save(update_fields=["is_used", "claimed_by", "claimed_at"])

                # An order can only be delivered when its code is attached.
                order_status = (
                    status
                    if status != OrderStatus.DELIVERED or code is not None
                    else OrderStatus.PENDING
                )

                with db_transaction.atomic():
                    order = Order.objects.create(
                        user=user,
                        product=product,
                        package=package,
                        group=group,
                        code=code,
                        product_name=product.name,
                        product_slug=product.slug,
                        category_name=product.category.name,
                        package_name=package.name,
                        group_name=group.name if group else "",
                        price=package.price,
                        status=order_status,
                    )
                    Transaction.objects.create(
                        user=user,
                        kind=TransactionKind.ORDER,
                        amount=package.price,
                        method="Purchase",
                        note=f"Order {order.pk}",
                        order=order,
                    )
                    created += 1

                order.created_at = algeria_now() - timedelta(
                    days=index * 4
                )
                Order.objects.filter(pk=order.pk).update(created_at=order.created_at)

            self.stdout.write(
                self.style.SUCCESS(f"{user.email}: demo orders created")
            )

        self.stdout.write(self.style.SUCCESS(f"Created {created} orders."))
