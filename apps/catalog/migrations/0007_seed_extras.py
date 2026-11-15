from django.utils.text import slugify

from django.db import migrations

EXTRAS = [
    ("templates", "Portfolio Template Pack", "12 portfolio layouts for designers and creatives.", "19.99"),
    ("templates", "Notion Dashboard Template", "An all-in-one planner and dashboard template.", "12.99"),
    ("assets", "3D Gradient Shapes Pack", "120 editable 3D gradient renders for motion and web.", "14.99"),
    ("assets", "LUTs & Film Presets", "Cinematic color grades for photo and video work.", "9.99"),
    ("scripts-starters", "Django API Boilerplate", "Production-ready Django REST starter with JWT auth.", "29.99"),
    ("scripts-starters", "Flutter E-commerce Starter", "Cross-platform store app with payments wired in.", "34.99"),
    ("ui-kits", "SaaS Landing UI Kit", "Marketing site blocks and pricing sections in Figma.", "24.99"),
    ("ui-kits", "Fintech Mobile UI Kit", "Banking-grade mobile screens with charts and cards.", "22.99"),
    ("marketing", "Email Sequence Vault", "30 ready-to-send lifecycle and launch sequences.", "16.99"),
    ("marketing", "Ad Creative Bundle", "200 tested ad layouts for paid social campaigns.", "19.99"),
    ("ai-automation", "AI Image Prompt Pack", "1,000 curated prompts for image generation models.", "11.99"),
    ("ai-automation", "Automation Workflow Library", "40 ready-made n8n and Make automation workflows.", "27.99"),
]


def create_extras(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    Package = apps.get_model("catalog", "Package")

    for slug, name, short_description, price in EXTRAS:
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            continue
        product, _ = Product.objects.get_or_create(
            slug=slugify(name),
            defaults={
                "category": category,
                "name": name,
                "type": "immediate",
                "short_description": short_description,
                "description": (
                    f"{short_description} Delivered instantly to your account. "
                    "Buy once, download forever — updates included."
                ),
            },
        )
        Package.objects.get_or_create(
            product=product,
            name="Standard",
            defaults={
                "price": price,
                "stock": None,
                "delivery_url": "https://example.com/delivery",
            },
        )


def remove_extras(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for slug, name, short_description, price in EXTRAS:
        Product.objects.filter(name=name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0006_media_fields"),
    ]

    operations = [
        migrations.RunPython(create_extras, remove_extras),
    ]
