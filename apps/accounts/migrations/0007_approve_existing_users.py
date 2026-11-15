"""Approve the accounts that already existed before the approval flow.

Accounts created after this migration start unapproved and wait for an admin.
"""

from django.db import migrations


def approve_existing_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.update(is_approved=True)


def unapprove_existing_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.update(is_approved=False)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0006_user_approved_at_user_is_approved")]

    operations = [migrations.RunPython(approve_existing_users, unapprove_existing_users)]
