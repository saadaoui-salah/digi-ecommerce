"""The figures of the catalog that need more than a query.

They live here so the signals, the admin dashboard and the tests all read the
same number.
"""

from decimal import Decimal

from .models import ItemType, Package


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
