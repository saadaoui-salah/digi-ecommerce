"""The money helpers of the shop.

Every price is in Algerian dinars (``DA``) and kept with two decimals, so the
figures read the same everywhere.
"""

from decimal import Decimal

#: Two decimals, the precision of every price of the shop.
CENTS = Decimal("0.01")

#: The currency of the shop.
CURRENCY = "DA"


def money(value) -> str:
    """A figure of the shop, as it is written everywhere: ``12.50 DA``."""
    return f"{Decimal(value or 0):.2f} {CURRENCY}"


def percentage(part, whole) -> Decimal:
    """``part`` as a percentage of ``whole``.

    It is the margin of a sale: what the shop earned on it, over what it was
    worth. A whole of zero means no percentage at all.
    """
    whole = Decimal(whole or 0)
    if not whole:
        return Decimal("0.00")

    return (Decimal(part or 0) / whole * 100).quantize(CENTS)
