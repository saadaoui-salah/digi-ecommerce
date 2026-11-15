"""Roll the daily sales rows up into the monthly ones.

Run it after the daily job:

    python manage.py aggregate_monthly
"""

from django.core.management.base import BaseCommand

from apps.analytics.services import run_monthly


class Command(BaseCommand):
    help = "Rebuild the monthly sales aggregates from the daily rows."

    def handle(self, *args, **options):
        written = run_monthly()
        self.stdout.write(
            self.style.SUCCESS(f"Monthly aggregates refreshed ({written} rows).")
        )
