from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    FilterSet,
    NumberFilter,
)

from django.db.models import Min, Q

from .models import Category, ItemType, Product
from .promotions import current_promotions


class CategoryFilter(FilterSet):
    parent = NumberFilter(field_name="parent_id")
    root = BooleanFilter(method="filter_root")

    class Meta:
        model = Category
        fields = ("parent",)

    def filter_root(self, queryset, name, value):
        return queryset.filter(parent__isnull=value)


class ProductFilter(FilterSet):
    category = NumberFilter(method="filter_category")
    category_slug = CharFilter(method="filter_category_slug")
    type = ChoiceFilter(choices=ItemType.choices, method="filter_type")
    available = BooleanFilter(field_name="is_available")
    promoted = BooleanFilter(method="filter_promoted")
    min_price = NumberFilter(field_name="price_from", lookup_expr="gte")
    max_price = NumberFilter(field_name="price_from", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ("category", "category_slug", "type", "available", "promoted")

    def _category_ids(self, value):
        return list(
            Category.objects.filter(Q(pk=value) | Q(parent_id=value)).values_list(
                "pk", flat=True
            )
        )

    def filter_type(self, queryset, name, value):
        # The type lives on packages; ProductViewSet annotates the first one.
        return queryset.filter(package_type=value)

    def filter_category(self, queryset, name, value):
        return queryset.filter(category_id__in=self._category_ids(value))

    def filter_category_slug(self, queryset, name, value):
        try:
            category = Category.objects.get(slug=value)
        except Category.DoesNotExist:
            return queryset.none()
        return queryset.filter(category_id__in=self._category_ids(category.pk))

    def filter_promoted(self, queryset, name, value):
        """Only the products a current promotion applies to (or the rest)."""
        rows = list(
            queryset.annotate(
                price_from=Min(
                    "packages__price", filter=Q(packages__is_active=True)
                )
            ).values("id", "category_id", "price_from")
        )
        promoted_ids = list(current_promotions(rows))
        if value:
            return queryset.filter(pk__in=promoted_ids)
        return queryset.exclude(pk__in=promoted_ids)
