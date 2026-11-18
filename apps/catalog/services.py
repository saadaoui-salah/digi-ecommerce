"""The figures of the catalog that need more than a query.

They live here so the signals, the admin dashboard and the tests all read the
same number.
"""

from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import User

from .models import ItemType, Package, PackageCode


def move_stock(package, delta: int):
    """Add or take a code away from the stock of the package."""
    package.stock = max(0, (package.stock or 0) + delta)
    package.save(update_fields=["stock"])


def move_stock_worth(package, delta: int):
    """Move the worth of the unsold stock on the staff accounts."""
    if not delta:
        return

    worth = Decimal(package.price) * delta
    User.objects.filter(is_staff=True).update(stock_worth=F("stock_worth") + worth)


def move_stock_quantity(delta: int):
    """Move the number of codes that are waiting to be sold."""
    if not delta:
        return

    User.objects.filter(is_staff=True).update(
        stock_quantity=F("stock_quantity") + delta
    )


def code_left_stock(package):
    """A code was sold or deleted: take it out of the stock figures."""
    if package.type != ItemType.IMMEDIATE:
        return

    move_stock(package, -1)
    move_stock_worth(package, -1)
    move_stock_quantity(-1)


def code_joined_stock(package):
    """A new code was added: put it in the stock figures."""
    if package.type != ItemType.IMMEDIATE:
        return

    move_stock(package, 1)
    move_stock_worth(package, 1)
    move_stock_quantity(1)


@transaction.atomic
def claim_next_code(package, user):
    """Claim one unused code of a package for a customer.

    The condition lives in the UPDATE itself, so the database decides who got
    the code: only one of two customers arriving at the same moment can win.
    It works on every backend — including SQLite, where Django's
    ``select_for_update`` is a no-op.

    ``None`` means another customer took the last code in the meantime.
    """
    candidates = PackageCode.objects.filter(
        package=package, is_used=False
    ).order_by("created_at", "id")

    for code in candidates.iterator():
        claimed_at = timezone.now()
        claimed = PackageCode.objects.filter(pk=code.pk, is_used=False).update(
            is_used=True,
            claimed_by=user,
            claimed_at=claimed_at,
        )
        if claimed:
            # The update bypassed the signals, so the figures are moved here.
            # The in-memory row is updated too, for the response.
            code.is_used = True
            code.claimed_by = user
            code.claimed_at = claimed_at
            code_left_stock(package)
            return code

    return None


def unsold_stock_quantity() -> int:
    """How many codes are still waiting to be sold.

    It is the stock of every instant package added up. The demand packages
    are left out: they are delivered by hand, so nothing sits in the store
    waiting.
    """
    return sum(
        package.stock or 0
        for package in Package.objects.filter(type=ItemType.IMMEDIATE).only("stock")
    )


def unsold_stock_worth() -> Decimal:
    """The worth of the codes that are still waiting to be sold.

    It is the stock of every instant package — the codes it still holds —
    times the price they would be sold for. The demand packages are left out:
    they are delivered by hand, so nothing sits in the store waiting.
    """
    total = Decimal("0.00")

    for package in Package.objects.filter(type=ItemType.IMMEDIATE).only(
        "stock", "price"
    ):
        total += Decimal(package.stock or 0) * Decimal(package.price)

    return total
