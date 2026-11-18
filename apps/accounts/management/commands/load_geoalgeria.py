"""Load the French wilaya and daira names from the bundled GeoAlgeria data.

The data is committed under data/geoalgeria/ so a deployment can populate a
fresh database without network access. Regions are deliberately not created:
staff group wilayas into regions later from the admin.

Usage: python manage.py load_geoalgeria
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Daira, Wilaya

DATA_DIR = Path(settings.BASE_DIR) / "data" / "geoalgeria"


class Command(BaseCommand):
    help = "Load wilayas and dairas from the bundled GeoAlgeria dataset"

    def handle(self, *args, **options):
        wilayas_path = DATA_DIR / "wilayas.json"
        dairas_path = DATA_DIR / "dairas.json"
        for path in (wilayas_path, dairas_path):
            if not path.exists():
                raise CommandError(f"Missing GeoAlgeria data file: {path}")

        with wilayas_path.open(encoding="utf-8") as handle:
            wilaya_rows = json.load(handle)["wilayas"]
        with dairas_path.open(encoding="utf-8") as handle:
            daira_rows = json.load(handle)

        codes = {row["code"]: row["name_fr"] for row in wilaya_rows}

        created_wilayas = 0
        created_dairas = 0
        with transaction.atomic():
            wilayas = {}
            for code, name in codes.items():
                wilaya, created = Wilaya.objects.get_or_create(
                    name=name,
                    defaults={"region": None, "is_active": True},
                )
                wilayas[code] = wilaya
                created_wilayas += int(created)

            for row in daira_rows:
                wilaya = wilayas.get(row["wilaya_code"])
                if wilaya is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Skipping daira {row['name_fr']}: unknown wilaya code {row['wilaya_code']}"
                        )
                    )
                    continue
                _, created = Daira.objects.get_or_create(
                    wilaya=wilaya,
                    name=row["name_fr"],
                    defaults={"is_active": True},
                )
                created_dairas += int(created)

        self.stdout.write(
            self.style.SUCCESS(
                f"GeoAlgeria loaded: {created_wilayas} new wilayas, "
                f"{created_dairas} new dairas "
                f"({len(wilayas)} wilayas, {len(daira_rows)} dairas in the source)."
            )
        )
