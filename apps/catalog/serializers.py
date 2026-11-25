from decimal import Decimal

from rest_framework import serializers

from apps.accounts.models import Coupon

from .models import (
    Category,
    Package,
    PackageCode,
    PackageGroup,
    Product,
    ProductImage,
    Promotion,
)


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True, default=0)
    sales_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    net_profit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    total_benefit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    pending_demand_orders = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "parent",
            "image",
            "products_count",
            "sales_count",
            "total_revenue",
            "net_profit",
            "total_benefit",
            "pending_demand_orders",
        )


class PromotionSerializer(serializers.ModelSerializer):
    base_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = Promotion
        fields = (
            "id",
            "name",
            "product",
            "category",
            "percentage",
            "discounted_price",
            "base_price",
            "starts_at",
            "ends_at",
            "is_active",
            "is_current",
            "created_at",
        )
        read_only_fields = ("id", "base_price", "is_current", "created_at")


class PackageSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    codes_available = serializers.IntegerField(read_only=True, default=0)
    price_current = serializers.SerializerMethodField()
    cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    margin = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    sales_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    net_profit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    total_benefit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )

    class Meta:
        model = Package
        fields = (
            "id",
            "product",
            "product_name",
            "group",
            "name",
            "type",
            "price",
            "price_current",
            "cost",
            "margin",
            "stock",
            "is_available",
            "codes_available",
            "sort_order",
            "sales_count",
            "total_revenue",
            "net_profit",
            "total_benefit",
        )

    def get_price_current(self, obj):
        promotion = self.context.get("promotion_for_product", {}).get(obj.product_id)
        price = obj.price
        if promotion is not None:
            price = promotion.price_for(price)
        return f"{Decimal(price):.2f}"


class PackageCodeSerializer(serializers.ModelSerializer):
    email = serializers.CharField(read_only=True)
    password = serializers.CharField(read_only=True)
    product_name = serializers.CharField(source="package.product.name", read_only=True)
    package_name = serializers.CharField(source="package.name", read_only=True)
    product_slug = serializers.CharField(source="package.product.slug", read_only=True)

    class Meta:
        model = PackageCode
        fields = (
            "id",
            "package",
            "email",
            "password",
            "product_name",
            "product_slug",
            "package_name",
            "claimed_at",
        )


class PackageGroupSerializer(serializers.ModelSerializer):
    packages = PackageSerializer(many=True, read_only=True)

    class Meta:
        model = PackageGroup
        fields = ("id", "product", "name", "is_active", "sort_order", "packages")


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    price_from = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    price_current = serializers.SerializerMethodField()
    promotion = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(read_only=True)
    sales_count = serializers.IntegerField(read_only=True)
    total_revenue = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    net_profit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    total_benefit = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    pending_demand_orders = serializers.IntegerField(read_only=True)

    def get_category_name(self, obj):
        return obj.category.name if obj.category_id else ""

    def get_category_slug(self, obj):
        return obj.category.slug if obj.category_id else ""

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "type",
            "slug",
            "category",
            "category_name",
            "category_slug",
            "short_description",
            "image",
            "video",
            "requires_info",
            "price_from",
            "price_current",
            "promotion",
            "is_available",
            "sales_count",
            "total_revenue",
            "net_profit",
            "total_benefit",
            "pending_demand_orders",
            "created_at",
        )

    def _promotion(self, obj):
        promotions = self.context.get("promotion_for_product", {})
        return promotions.get(obj.id)

    def get_price_current(self, obj):
        price = obj.price_from
        if price is None:
            return None
        promotion = self._promotion(obj)
        if promotion is not None:
            price = promotion.price_for(price)
        return f"{Decimal(price):.2f}"

    def get_promotion(self, obj):
        promotion = self._promotion(obj)
        if promotion is None:
            return None
        return {
            "id": promotion.id,
            "name": promotion.name,
            "percentage": str(promotion.percentage) if promotion.percentage is not None else None,
            "discounted_price": (
                str(promotion.discounted_price)
                if promotion.discounted_price is not None
                else None
            ),
            "ends_at": promotion.ends_at,
        }


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "sort_order")


class CouponSerializer(serializers.Serializer):
    """The coupon a customer has for a product."""

    code = serializers.CharField(read_only=True)
    percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True, allow_null=True
    )
    discount_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, allow_null=True
    )
    max_orders = serializers.IntegerField(read_only=True)
    used_orders = serializers.IntegerField(read_only=True)
    remaining_orders = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_price_of = serializers.SerializerMethodField()

    def get_remaining_orders(self, obj):
        return max(0, obj.max_orders - obj.used_orders)

    def get_price(self, obj):
        """The real price of the cheapest package of the product."""
        return f"{obj.reference_price:.2f}"

    def get_discount_price_of(self, obj):
        """The price the customer pays for that package."""
        return f"{obj.price_for(obj.reference_price):.2f}"


class ProductDetailSerializer(ProductSerializer):
    packages = PackageSerializer(many=True, read_only=True)
    package_groups = PackageGroupSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True, source="gallery_images")
    related = serializers.SerializerMethodField()
    coupon = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + (
            "description",
            "images",
            "packages",
            "package_groups",
            "related",
            "coupon",
        )

    def get_coupon(self, obj):
        """The coupon of the signed-in customer for this product, if any."""
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if user is None or not user.is_authenticated:
            return None

        coupon = (
            Coupon.objects.filter(user=user, product=obj, is_active=True)
            .order_by("-created_at", "-id")
            .first()
        )

        if coupon is None or not coupon.is_usable:
            return None

        return CouponSerializer(coupon).data

    def get_related(self, obj):
        """Other products from the same category, shipped with the detail."""
        related = self.context.get("related_products")
        if not related:
            return []
        return ProductSerializer(related, many=True, context=self.context).data
