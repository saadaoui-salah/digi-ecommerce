"""The worth of the stock that is not sold yet.

The stock of an instant package becomes the number of codes it holds, and the
worth of the unsold stock — the codes sitting in the store, at the price they
would be sold for — is kept on the staff accounts so the admin dashboard can
read it without walking the codes.
"""

from decimal import Decimal

from django.db import migrations, models


def backfill(apps, schema_editor):
    """Count the codes of the instant packages and price the unsold ones."""
    Package = apps.get_model("catalog", "Package")
    PackageCode = apps.get_model("catalog", "PackageCode")
    User = apps.get_model("accounts", "User")

    worth = Decimal("0.00")

    for package in Package.objects.filter(type="immediate"):
        codes = PackageCode.objects.filter(package=package, is_used=False).count()
        package.stock = codes
        package.save(update_fields=["stock"])
        worth += Decimal(package.price) * codes

    if worth:
        User.objects.filter(is_staff=True).update(stock_worth=worth)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0015_order_cost_user_total_benefit_alter_user_net_profit"),
        ("catalog", "0015_category_net_profit_category_pending_demand_orders_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="stock_worth",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text=(
                    "The worth of the stock the shop has not sold yet. It is a "
                    "figure of the shop, so only the staff accounts carry it "
                    "and the admin dashboard is the one that reads it."
                ),
                max_digits=14,
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
