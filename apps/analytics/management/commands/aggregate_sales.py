"""Refresh every period at once — handy for the first run and for a rebuild.

    python manage.py aggregate_sales
"""

from django.core.management.base import BaseCommand

from apps.analytics.services import run_daily, run_monthly, run_yearly


class Command(BaseCommand):
    help = "Refresh the daily, monthly and yearly sales aggregates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Rebuild every day from scratch instead of only the changed ones.",
        )

    def handle(self, *args, **options):
        full = options.get("full", False)

        daily = run_daily(full=full)
        monthly = run_monthly()
        yearly = run_yearly()

        self.stdout.write(
            self.style.SUCCESS(
                f"Aggregates refreshed — {daily} daily, {monthly} monthly, "
                f"{yearly} yearly rows."
            )
        )
