"""The stock of an instant package is the number of codes it holds.

Only the help text changes — the column was already there for the demand
packages.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0015_category_net_profit_category_pending_demand_orders_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="package",
            name="stock",
            field=models.PositiveIntegerField(
                blank=True,
                help_text=(
                    "Instant packages: how many codes they still hold — the "
                    "signals keep it up to date. Demand packages: how many can "
                    "still be sold."
                ),
                null=True,
            ),
        ),
    ]
