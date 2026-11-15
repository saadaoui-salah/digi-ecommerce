"""Fill instant packages with deliverable codes.

Each code is stored as ``email|password``. The command is idempotent: it only
creates the codes that are missing to reach the requested amount per package.

    python manage.py seed_codes --per-package 5
"""

import secrets
import string

from django.core.management.base import BaseCommand

from apps.catalog.models import ItemType, Package, PackageCode


def random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Create demo codes for instant packages."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-package",
            type=int,
            default=5,
            help="Minimum number of unused codes per instant package.",
        )
        parser.add_argument(
            "--password-length",
            type=int,
            default=12,
            help="Length of the generated passwords.",
        )

    def handle(self, *args, **options):
        per_package = options["per_package"]
        password_length = options["password_length"]

        packages = Package.objects.filter(
            is_active=True, product__type=ItemType.IMMEDIATE
        ).select_related("product")

        created = 0
        for package in packages:
            existing = package.codes.filter(is_used=False).count()
            missing = max(0, per_package - existing)
            if not missing:
                continue

            slug = package.product.slug
            for index in range(missing):
                email = f"{slug}.{package.id}.{index + 1}@demo.digi.store"
                password = random_password(password_length)
                PackageCode.objects.create(
                    package=package, code=f"{email}|{password}"
                )
                created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"{package.product.name} / {package.name}: +{missing} codes"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f"Created {created} package codes.")
        )
