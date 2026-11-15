"""Refresh the daily sales rows.

Run it every day (cron, task scheduler, …) so the daily figures stay fresh:

    python manage.py aggregate_daily

Only the days that changed are recomputed. Use ``--full`` to rebuild the
whole history, or ``--lookback`` to widen the window the job looks at.
"""

from django.core.management.base import BaseCommand

from apps.analytics.services import DEFAULT_LOOKBACK_DAYS, run_daily


class Command(BaseCommand):
    help = "Refresh the daily sales aggregates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Rebuild every day from scratch instead of only the changed ones.",
        )
        parser.add_argument(
            "--lookback",
            type=int,
            default=DEFAULT_LOOKBACK_DAYS,
            help=(
                "How many days back to look for new or resold orders "
                f"(default {DEFAULT_LOOKBACK_DAYS})."
            ),
        )

    def handle(self, *args, **options):
        written = run_daily(
            full=options.get("full", False),
            lookback_days=options.get("lookback", DEFAULT_LOOKBACK_DAYS),
        )
        self.stdout.write(
            self.style.SUCCESS(f"Daily aggregates refreshed ({written} rows).")
        )
