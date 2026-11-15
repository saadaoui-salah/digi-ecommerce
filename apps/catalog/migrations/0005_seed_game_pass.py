from django.db import migrations

COUNTRIES = [
    ("United States", [
        ("1 Month", "9.99", None, 0),
        ("2 Months", "18.99", None, 1),
        ("3 Months", "26.99", None, 2),
        ("12 Months", "79.99", None, 3),
    ]),
    ("Turkey", [
        ("1 Month", "4.99", None, 0),
        ("3 Months", "12.99", None, 1),
        ("6 Months", "22.99", None, 2),
    ]),
    ("Algeria", [
        ("1 Month", "5.99", None, 0),
        ("2 Months", "11.49", None, 1),
        ("6 Months", "29.99", None, 2),
    ]),
    ("India", [
        ("1 Month", "3.99", None, 0),
        ("3 Months", "10.99", None, 1),
        ("12 Months", "34.99", None, 2),
    ]),
]


def seed_game_pass(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    PackageGroup = apps.get_model("catalog", "PackageGroup")
    Package = apps.get_model("catalog", "Package")

    category, _ = Category.objects.get_or_create(
        slug="gaming",
        defaults={
            "name": "Gaming",
            "description": "Game passes, credits, and gaming memberships delivered instantly.",
        },
    )
    product, _ = Product.objects.get_or_create(
        slug="game-pass",
        defaults={
            "category": category,
            "name": "Game Pass",
            "type": "immediate",
            "short_description": "Game Pass membership by country — pick your region and duration.",
            "description": (
                "Official Game Pass membership delivered instantly. "
                "Choose your country, then pick a duration from 1 to 12 months. "
                "The code is delivered to your account right after checkout."
            ),
        },
    )

    for index, (country_name, durations) in enumerate(COUNTRIES):
        group, _ = PackageGroup.objects.get_or_create(
            product=product,
            name=country_name,
            defaults={"sort_order": index},
        )
        for name, price, stock, sort_order in durations:
            Package.objects.get_or_create(
                group=group,
                name=name,
                defaults={
                    "product": product,
                    "price": price,
                    "stock": stock,
                    "delivery_url": "https://example.com/game-pass",
                    "sort_order": sort_order,
                },
            )


def remove_game_pass(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.filter(slug="game-pass").delete()
    Category = apps.get_model("catalog", "Category")
    Category.objects.filter(slug="gaming").exclude(
        products__isnull=False
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_packagegroup"),
    ]

    operations = [
        migrations.RunPython(seed_game_pass, remove_game_pass),
    ]
