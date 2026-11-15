"""Link the existing transactions to the orders they paid for.

The transactions used to keep only "Order 12" in their note. Now that the
relation is stored, the older rows can be matched back to their order.

    python manage.py link_transactions
"""

import re

from django.core.management.base import BaseCommand

from apps.accounts.models import Order, Transaction

NOTE_PATTERN = re.compile(r"^Order #?(\d+)\s*$")


class Command(BaseCommand):
    help = "Link the transactions to their order using the note."

    def handle(self, *args, **options):
        linked = 0
        for transaction in Transaction.objects.filter(order__isnull=True).iterator():
            match = NOTE_PATTERN.match(transaction.note.strip())
            if not match:
                continue
            order = Order.objects.filter(pk=int(match.group(1))).first()
            if order is None:
                continue
            Transaction.objects.filter(pk=transaction.pk).update(order=order)
            linked += 1

        self.stdout.write(self.style.SUCCESS(f"Linked {linked} transactions."))
