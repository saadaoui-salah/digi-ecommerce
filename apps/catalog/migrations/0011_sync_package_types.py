"""Keep the package type in sync with the type of its product."""

from django.db import migrations


def sync_package_types(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for package in Package.objects.select_related("product").iterator():
        if package.type != package.product.type:
            package.type = package.product.type
            package.save(update_fields=["type"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_alter_package_stock")]

    operations = [migrations.RunPython(sync_package_types, migrations.RunPython.noop)]
