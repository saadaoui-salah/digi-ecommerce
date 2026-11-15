from django.db import transaction
from django.db.models import Count, Exists, Min, OuterRef, Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from apps.core.time import now as algeria_now

from .filters import CategoryFilter, ProductFilter
from .models import (
    Category,
    ItemType,
    Package,
    PackageCode,
    PackageGroup,
    Product,
    ProductImage,
    Promotion,
)
from .promotions import current_promotions
from .serializers import (
    CategorySerializer,
    PackageCodeSerializer,
    PackageSerializer,
    ProductDetailSerializer,
    ProductSerializer,
    PromotionSerializer,
)


class SlugLookupMixin:
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup = self.kwargs.get(self.lookup_url_kwarg)

        if lookup is not None and str(lookup).isdigit():
            try:
                return get_object_or_404(queryset, pk=lookup)
            except Http404:
                pass
        return get_object_or_404(queryset, slug=lookup)


class CategoryViewSet(SlugLookupMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = CategoryFilter
    search_fields = ("name", "description")
    ordering_fields = ("name",)

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("parent")
            .annotate(
                products_count=Count("products", distinct=True)
                + Count("children__products", distinct=True),
            )
        )


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Packages, plus the delivery endpoint used to claim an instant code."""

    queryset = Package.objects.filter(is_active=True).select_related("product")
    serializer_class = PackageSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ("product", "group")
    ordering_fields = ("price", "sort_order")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(unused_codes=Count("codes", filter=Q(codes__is_used=False)))
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        products = (
            Product.objects.filter(
                pk__in=self.get_queryset().values("product_id")
            )
            .annotate(
                price_from=Min(
                    "packages__price", filter=Q(packages__is_active=True)
                )
            )
            .values("id", "category_id", "price_from")
        )
        context["promotion_for_product"] = current_promotions(list(products))
        return context

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def deliver(self, request, pk=None):
        """Claim one unused code of an instant package for the customer."""
        package = self.get_object()

        if package.type != ItemType.IMMEDIATE or package.product.type != ItemType.IMMEDIATE:
            return Response(
                {"detail": "This package is delivered on request, not instantly."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            code = (
                PackageCode.objects.select_for_update()
                .filter(package=package, is_used=False)
                .order_by("created_at", "id")
                .first()
            )

            if code is None:
                return Response(
                    {"detail": "No codes are left for this package."},
                    status=status.HTTP_409_CONFLICT,
                )

            if not package.is_active:
                return Response(
                    {"detail": "This package is sold out."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            code.is_used = True
            code.claimed_by = request.user
            code.claimed_at = algeria_now()
            code.save(update_fields=["is_used", "claimed_by", "claimed_at"])

            # The signal takes the code out of the stock of the package.
        return Response(
            PackageCodeSerializer(code).data, status=status.HTTP_201_CREATED
        )


class DeliveredCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """Codes the signed-in customer has claimed."""

    serializer_class = PackageCodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (
            PackageCode.objects.filter(
                claimed_by=self.request.user, is_used=True
            )
            .select_related("package", "package__product")
            .order_by("-claimed_at", "-id")
        )


class PromotionViewSet(viewsets.ReadOnlyModelViewSet):
    """The promotions that are running right now."""

    serializer_class = PromotionSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ("product", "category")
    ordering_fields = ("created_at", "ends_at")

    def get_queryset(self):
        return Promotion.objects.filter(is_active=True).select_related(
            "product", "category"
        )


class ProductViewSet(SlugLookupMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = ProductFilter
    search_fields = ("name", "short_description", "description")
    ordering_fields = ("name", "price_from", "created_at")

    def base_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .annotate(
                price_from=Min(
                    "packages__price", filter=Q(packages__is_active=True)
                ),
                is_available=Exists(
                    Package.objects.filter(
                        product=OuterRef("pk"), is_active=True
                    ).filter(
                        # Demand packages are limited by stock, instant packages
                        # by the codes they still hold.
                        (Q(type=ItemType.DEMAND))
                        & (Q(stock__isnull=True) | Q(stock__gt=0))
                        | (Q(type=ItemType.IMMEDIATE) & Q(codes__is_used=False))
                    )
                ),
            )
            .order_by("-created_at")
        )

    def get_queryset(self):
        queryset = self.base_queryset()
        if self.action == "retrieve":
            active_packages = Package.objects.filter(is_active=True).annotate(
                unused_codes=Count("codes", filter=Q(codes__is_used=False))
            )
            queryset = queryset.prefetch_related(
                Prefetch("packages", queryset=active_packages),
                Prefetch(
                    "gallery_images",
                    queryset=ProductImage.objects.order_by("sort_order", "id"),
                ),
                Prefetch(
                    "package_groups",
                    queryset=PackageGroup.objects.filter(is_active=True).prefetch_related(
                        Prefetch("packages", queryset=active_packages)
                    ),
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        queryset = self.get_queryset()
        rows = list(queryset.values("id", "category_id", "price_from"))
        rows += [
            {
                "id": product.id,
                "category_id": product.category_id,
                "price_from": product.price_from,
            }
            for product in getattr(self, "_related_products", [])
        ]
        context["promotion_for_product"] = current_promotions(rows)
        return context

    def retrieve(self, request, *args, **kwargs):
        """Serve the detail with its siblings in one response."""
        product = self.get_object()
        # The detail page needs the sibling products too, so they travel with
        # the product instead of costing a second request.
        self._related_products = list(
            self.base_queryset()
            .filter(category_id=product.category_id)
            .exclude(pk=product.pk)
            .order_by("-created_at")[:3]
        )
        serializer = self.get_serializer(product)
        serializer.context["related_products"] = self._related_products
        return Response(serializer.data)
