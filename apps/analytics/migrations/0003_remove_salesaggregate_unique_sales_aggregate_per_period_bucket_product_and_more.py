"""Give every figure a customer.

The rows used to belong to the shop as a whole. Each one now belongs to the
customer who made the orders behind it, so every customer sees their own
figures and the shop is the sum of them.

The old rows cannot be split — they do not say who bought what — so they are
cleared here and the aggregation job rebuilds them from the orders:

    python manage.py aggregate_sales --full
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def clear_rows(apps, schema_editor):
    """Drop the rows that do not belong to a customer yet."""
    SalesAggregate = apps.get_model("analytics", "SalesAggregate")
    SalesAggregate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_alter_analyticsrun_ran_at'),
        ('catalog', '0015_category_net_profit_category_pending_demand_orders_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(clear_rows, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='salesaggregate',
            name='unique_sales_aggregate_per_period_bucket_product',
        ),
        migrations.RemoveIndex(
            model_name='salesaggregate',
            name='analytics_s_period_09e031_idx',
        ),
        migrations.AddField(
            model_name='salesaggregate',
            name='user',
            field=models.ForeignKey(help_text='The customer this row belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='sales_aggregates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='salesaggregate',
            index=models.Index(fields=['user', 'period', 'bucket'], name='analytics_s_user_id_f14257_idx'),
        ),
        migrations.AddConstraint(
            model_name='salesaggregate',
            constraint=models.UniqueConstraint(fields=('user', 'period', 'bucket', 'product'), name='unique_sales_aggregate_per_user_period_bucket_product'),
        ),
    ]
