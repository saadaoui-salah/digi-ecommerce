"""Roll the daily sales rows up into the yearly ones.

Run it after the daily job:

    python manage.py aggregate_yearly
"""

from django.core.management.base import BaseCommand

from apps.analytics.services import run_yearly


class Command(BaseCommand):
    help = "Rebuild the yearly sales aggregates from the daily rows."

    def handle(self, *args, **options):
        written = run_yearly()
        self.stdout.write(
            self.style.SUCCESS(f"Yearly aggregates refreshed ({written} rows).")
        )
