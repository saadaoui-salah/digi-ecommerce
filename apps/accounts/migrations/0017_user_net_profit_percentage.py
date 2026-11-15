"""The net profit as a percentage.

The margin of the shop: the net profit over the price of the packages sold.
The signals keep it in step with the two figures it is made of, so the page
never has to divide anything.
"""

from decimal import Decimal

from django.db import migrations, models


def backfill(apps, schema_editor):
    """Compute the percentage of every customer from their counters."""
    User = apps.get_model("accounts", "User")

    for account in User.objects.all().iterator():
        revenue = Decimal(account.total_revenue or 0)
        profit = Decimal(account.net_profit or 0)

        percentage = Decimal("0.00")
        if revenue:
            percentage = (profit / revenue * 100).quantize(Decimal("0.01"))

        account.net_profit_percentage = percentage
        account.save(update_fields=["net_profit_percentage"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0016_user_stock_worth"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="net_profit_percentage",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text=(
                    "The net profit as a percentage of what the customer paid: "
                    "the price of the packages sold minus their cost, over the "
                    "price of the packages sold. The signals keep it up to "
                    "date."
                ),
                max_digits=7,
            ),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
