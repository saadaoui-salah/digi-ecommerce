"""Reactions to the catalog rows.

The stock of an instant package is the number of codes it still holds. The
signals keep it in step with the codes: a new code adds one, a code that is
sold or deleted takes one away.

They also keep the figures of the unsold stock on the staff accounts: how
many codes are waiting to be sold and what they are worth. Those are figures
of the shop — the codes sitting in the store, at the price they would be sold
for — so every staff account carries the same numbers and the admin page
reads them from there.
"""

from decimal import Decimal

from django.db.models import F
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.accounts.models import User

from .models import ItemType, PackageCode


def _move_stock(package, delta: int):
    """Add or take one code away from the stock of the package."""
    package.stock = max(0, (package.stock or 0) + delta)
    package.save(update_fields=["stock"])


def _move_stock_worth(package, delta: int):
    """Move the worth of the unsold stock on the staff accounts."""
    if not delta:
        return

    worth = Decimal(package.price) * delta
    User.objects.filter(is_staff=True).update(stock_worth=F("stock_worth") + worth)


def _move_stock_quantity(delta: int):
    """Move the number of codes that are waiting to be sold."""
    if not delta:
        return

    User.objects.filter(is_staff=True).update(
        stock_quantity=F("stock_quantity") + delta
    )


@receiver(pre_save, sender=PackageCode)
def remember_code_before_save(sender, instance, **kwargs):
    """Stash whether the code was already sold.

    The signal that moves the stock runs after the save, so it needs to know
    whether the code was already out of the stock.
    """
    if not instance.pk:
        instance._was_used = False
        return

    instance._was_used = (
        PackageCode.objects.filter(pk=instance.pk)
        .values_list("is_used", flat=True)
        .first()
    )


@receiver(post_save, sender=PackageCode)
def track_code_stock(sender, instance, created, **kwargs):
    """Keep the stock of the package and the figures of the unsold stock.

    A new code joins the stock, a code that is sold leaves it. Only instant
    packages hold codes, so the demand ones are left alone.
    """
    package = instance.package
    if package.type != ItemType.IMMEDIATE:
        return

    if created:
        _move_stock(package, 1)
        _move_stock_worth(package, 1)
        _move_stock_quantity(1)
        return

    if instance.is_used and not getattr(instance, "_was_used", False):
        # The code was sold: it is no longer part of the unsold stock.
        _move_stock(package, -1)
        _move_stock_worth(package, -1)
        _move_stock_quantity(-1)


@receiver(post_delete, sender=PackageCode)
def forget_code_stock(sender, instance, **kwargs):
    """Take a deleted code out of the stock.

    A code that was already sold left the stock when it was sold, so only an
    unused one still counts.
    """
    package = instance.package
    if package.type != ItemType.IMMEDIATE:
        return

    if not instance.is_used:
        _move_stock(package, -1)
        _move_stock_worth(package, -1)
        _move_stock_quantity(-1)
