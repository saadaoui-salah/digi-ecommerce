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

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import ItemType, PackageCode
from .services import code_joined_stock, code_left_stock


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
        code_joined_stock(package)
        return

    if instance.is_used and not getattr(instance, "_was_used", False):
        # The code was sold: it is no longer part of the unsold stock.
        code_left_stock(package)


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
        code_left_stock(package)
