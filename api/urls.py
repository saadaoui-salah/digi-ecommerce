from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import SimpleRouter

from apps.catalog.views import (
    CategoryViewSet,
    DeliveredCodeViewSet,
    PackageViewSet,
    ProductViewSet,
    PromotionViewSet,
)

router = SimpleRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("products", ProductViewSet, basename="product")
router.register("packages", PackageViewSet, basename="package")
router.register("codes", DeliveredCodeViewSet, basename="code")
router.register("promotions", PromotionViewSet, basename="promotion")


def api_root(request):
    return JsonResponse(
        {
            "auth": request.build_absolute_uri("/api/auth/"),
            "categories": request.build_absolute_uri("/api/categories/"),
            "products": request.build_absolute_uri("/api/products/"),
            "packages": request.build_absolute_uri("/api/packages/"),
            "codes": request.build_absolute_uri("/api/codes/"),
            "promotions": request.build_absolute_uri("/api/promotions/"),
            "schema": request.build_absolute_uri("/api/schema/"),
        }
    )


urlpatterns = [
    path("", api_root, name="api-root"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("auth/", include("apps.accounts.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", include(router.urls)),
]
