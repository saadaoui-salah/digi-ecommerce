import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0022_order_code_one_to_one"),
    ]

    operations = [
        # Keep the existing rows: rename the table and the FK column instead
        # of dropping and recreating the model.
        migrations.RenameModel(
            old_name="Balladia",
            new_name="Daira",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="balladia",
            new_name="daira",
        ),
        migrations.AlterModelOptions(
            name="daira",
            options={
                "ordering": ("wilaya__name", "name"),
                "verbose_name_plural": "dairas",
            },
        ),
        migrations.AlterField(
            model_name="wilaya",
            name="region",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="wilayas",
                to="accounts.region",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="daira",
            name="accounts_balladia_unique_per_wilaya",
        ),
        migrations.AddConstraint(
            model_name="daira",
            constraint=models.UniqueConstraint(
                fields=("wilaya", "name"),
                name="accounts_daira_unique_per_wilaya",
            ),
        ),
        migrations.AlterField(
            model_name="daira",
            name="wilaya",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="dairas",
                to="accounts.wilaya",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="daira",
            field=models.ForeignKey(
                blank=True,
                help_text="The daira the customer lives in.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="customers",
                to="accounts.daira",
            ),
        ),
    ]
