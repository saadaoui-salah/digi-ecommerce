"""Create demo credit transactions so the customer history is not empty.

Creating a transaction updates the customer's credit balance, so this command
is idempotent: users that already have transactions are skipped.

    python manage.py seed_transactions
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from datetime import timedelta

from apps.accounts.models import Transaction, TransactionKind
from apps.core.time import now as algeria_now

User = get_user_model()

DEMO_TRANSACTIONS = [
    (TransactionKind.CREDIT, "5000.00", "Bank transfer", "Welcome top-up"),
    (TransactionKind.CREDIT, "2500.00", "Cash", "Order #ORD-1038"),
    (TransactionKind.ORDER, "1500.00", "Purchase", "Game Pass Key"),
    (TransactionKind.REFUND, "1500.00", "Purchase", "Refund for Game Pass Key"),
]


class Command(BaseCommand):
    help = "Create demo credit transactions for customers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            help="Only seed this customer (defaults to every customer).",
        )

    def handle(self, *args, **options):
        users = User.objects.filter(is_superuser=False)
        if options.get("email"):
            users = users.filter(email__iexact=options["email"])

        created = 0
        for user in users:
            if user.transactions.exists():
                continue

            with db_transaction.atomic():
                for index, (kind, amount, method, note) in enumerate(
                    DEMO_TRANSACTIONS
                ):
                    Transaction.objects.create(
                        user=user,
                        kind=kind,
                        amount=amount,
                        method=method,
                        note=note,
                        created_by=None,
                    )
                    created += 1

            # Spread the demo transactions over the last weeks.
            transactions = list(user.transactions.order_by("created_at"))
            now = algeria_now()
            for offset, record in enumerate(transactions):
                record.created_at = now - timedelta(days=offset * 5)
                Transaction.objects.filter(pk=record.pk).update(
                    created_at=record.created_at
                )

            self.stdout.write(
                self.style.SUCCESS(f"{user.email}: {len(transactions)} transactions")
            )

        self.stdout.write(self.style.SUCCESS(f"Created {created} transactions."))
