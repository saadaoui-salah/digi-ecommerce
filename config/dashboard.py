"""The figures of the admin dashboard.

The dashboard of the admin shows the size of the shop at a glance; the
figures themselves live on their own page (**Admin → Analytics**).
"""

from django.contrib.auth import get_user_model

from apps.catalog.models import Category, Package, Product


def dashboard_callback(request, context):
    """The counts of the shop, shown on the admin dashboard."""
    User = get_user_model()

    context.update(
        {
            "stats": {
                "customers": User.objects.count(),
                "categories": Category.objects.filter(is_active=True).count(),
                "products": Product.objects.filter(is_active=True).count(),
                "packages": Package.objects.filter(is_active=True).count(),
            },
        }
    )
    return context
