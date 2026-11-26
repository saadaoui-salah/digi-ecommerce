import re
from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Daira,
    Credit,
    CreditKind,
    Notification,
    Order,
    OrderReport,
    Referral,
    Transaction,
    User,
    Wilaya,
)
from ..catalog.models import Package


class DairaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Daira
        fields = ("id", "name", "wilaya", "is_active")


class WilayaOptionSerializer(serializers.ModelSerializer):
    """Public wilaya option — regions stay an admin-only concept."""

    class Meta:
        model = Wilaya
        fields = ("id", "name")


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True, max_length=150)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=True, max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)
    wilaya = serializers.PrimaryKeyRelatedField(
        queryset=Wilaya.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    daira = serializers.PrimaryKeyRelatedField(
        queryset=Daira.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=32,
        write_only=True,
        help_text="The code of the referral link the account was opened with.",
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "credit",
            "password",
            "referral_code",
            "wilaya",
            "daira",
        )
        read_only_fields = ("id", "credit")

    def validate(self, attrs):
        """The daira has to be inside the wilaya that was picked."""
        wilaya = attrs.get("wilaya")
        daira = attrs.get("daira")

        if wilaya and daira and daira.wilaya_id != wilaya.id:
            raise serializers.ValidationError(
                {"daira": "That daira is not in the chosen wilaya."}
            )

        return attrs

    def create(self, validated_data):
        referral_code = validated_data.pop("referral_code", "")

        # The referral travels in a cookie, so it is picked up even when the
        # visitor reloads the page before opening the account.
        if not referral_code:
            request = self.context.get("request")
            referral_code = (request.COOKIES.get("digi_ref") or "") if request else ""

        if not validated_data.get("username"):
            validated_data["username"] = self._unique_username(
                validated_data["email"]
            )
        user = User.objects.create_user(**validated_data)

        # The account was opened through a referral link: the customer who
        # shared it is remembered.
        if referral_code:
            referrer = User.objects.filter(
                referral_code=referral_code.strip().upper(),
                accepts_referrals=True,
            ).first()
            if referrer is not None and referrer.pk != user.pk:
                user.referred_by = referrer
                user.save(update_fields=["referred_by"])

        return user

    def validate_referral_code(self, value):
        return (value or "").strip().upper()

    def validate_email(self, value):
        value = value.strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_phone(self, value):
        value = re.sub(r"[\s().-]", "", value.strip())
        if not re.fullmatch(r"\+?\d{7,15}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )
        return value

    @staticmethod
    def _unique_username(email):
        base = re.sub(r"[^a-z0-9_.+-]", "", email.split("@")[0].lower())[:140]
        base = base or "user"
        username = base
        suffix = 2
        while User.objects.filter(username__iexact=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        return username


class ReferralSerializer(serializers.ModelSerializer):
    """One earning of the referral program."""

    referred_email = serializers.EmailField(source="referred.email", read_only=True)
    referred_name = serializers.SerializerMethodField()
    order_total = serializers.DecimalField(
        source="order.price", max_digits=12, decimal_places=2, read_only=True
    )
    product_name = serializers.CharField(
        source="order.product_name", read_only=True
    )

    class Meta:
        model = Referral
        fields = (
            "id",
            "referred",
            "referred_email",
            "referred_name",
            "order",
            "order_total",
            "product_name",
            "amount",
            "percentage",
            "created_at",
        )
        read_only_fields = fields

    def get_referred_name(self, obj):
        return obj.referred.get_full_name() or obj.referred.username


class ReferralProgramSerializer(serializers.ModelSerializer):
    """The referral program of a customer: their link and what they earned."""

    code = serializers.CharField(source="referral_code", read_only=True)
    percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    accepts_referrals = serializers.BooleanField(read_only=True)
    total_earned = serializers.SerializerMethodField()
    referred_count = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "code",
            "percentage",
            "accepts_referrals",
            "total_earned",
            "referred_count",
            "earnings",
        )
        read_only_fields = fields

    def get_total_earned(self, obj):
        total = obj.referrals_given.aggregate(total=Sum("amount"))["total"]
        return f"{Decimal(total or 0):.2f}"

    def get_referred_count(self, obj):
        return obj.referrals_given.count()

    def get_earnings(self, obj):
        earnings = obj.referrals_given.select_related(
            "referred", "order"
        ).all()[:100]
        return ReferralSerializer(earnings, many=True).data


class LoginSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop(self.username_field, None)
        self.fields["email"] = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email__iexact=attrs["email"]).first()
        if user is None or not user.is_active or not user.check_password(
            attrs["password"]
        ):
            raise AuthenticationFailed("Invalid email or password.")

        self.user = user
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "credit",
            "owed",
            "free_spend",
            "is_approved",
            "is_staff",
            "total_revenue",
            "net_profit",
            "net_profit_percentage",
            "total_benefit",
            "orders_count",
            "pending_demand_orders",
            "accepts_referrals",
            "referral_percentage",
            "referral_code",
            "date_joined",
        )
        read_only_fields = (
            "id",
            "username",
            "credit",
            "owed",
            "free_spend",
            "is_approved",
            "is_staff",
            "total_revenue",
            "net_profit",
            "net_profit_percentage",
            "total_benefit",
            "orders_count",
            "pending_demand_orders",
            "accepts_referrals",
            "referral_percentage",
            "referral_code",
            "date_joined",
        )

    def validate_email(self, value):
        value = value.strip()
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_phone(self, value):
        value = re.sub(r"[\s().-]", "", value.strip())
        if not re.fullmatch(r"\+?\d{7,15}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        queryset = User.objects.filter(phone=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )
        return value


class NotificationSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "body",
            "is_read",
            "order_id",
            "created_at",
        )
        read_only_fields = fields


class OrderReportSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderReport
        fields = (
            "id",
            "order",
            "author",
            "author_name",
            "title",
            "details",
            "created_at",
        )
        read_only_fields = ("id", "order", "author", "author_name", "created_at")

    def get_author_name(self, obj):
        if obj.author is None:
            return ""
        return obj.author.get_full_name() or obj.author.username


class OrderSerializer(serializers.ModelSerializer):
    code_masked = serializers.CharField(read_only=True)
    code_ready = serializers.BooleanField(read_only=True)
    code_value = serializers.CharField(read_only=True)
    is_sold = serializers.BooleanField(read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    reports_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "product",
            "product_slug",
            "product_name",
            "category_name",
            "package",
            "package_name",
            "group",
            "group_name",
            "price",
            "quantity",
            "sold_price",
            "sold_at",
            "is_sold",
            "buyer_info",
            "status",
            "code_masked",
            "code_ready",
            "code_value",
            "assigned_to",
            "assigned_to_name",
            "reports_count",
            "created_at",
        )
        read_only_fields = fields

    def get_assigned_to_name(self, obj):
        if obj.assigned_to is None:
            return ""
        return obj.assigned_to.get_full_name() or obj.assigned_to.username

    def get_reports_count(self, obj):
        return getattr(obj, "reports_count", obj.reports.count())


class OrderSoldSerializer(serializers.Serializer):
    """Record what the customer resold this order for."""

    sold_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=True,
        allow_null=True,
    )


class OrderCreateSerializer(serializers.Serializer):
    package = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=100, default=1)
    buyer_info = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=True
    )

    def validate(self, attrs):
        package = (
            Package.objects.filter(pk=attrs["package"], is_active=True)
            .select_related("product", "product__category", "group")
            .first()
        )
        if package is None:
            raise serializers.ValidationError("That package is not available.")
        if not package.is_available:
            raise serializers.ValidationError("That package is sold out.")
        attrs["package_obj"] = package

        product = package.product
        buyer_info = attrs.get("buyer_info") or ""
        if package.requires_info and package.type == "demand" and not buyer_info:
            raise serializers.ValidationError(
                {"buyer_info": "Please provide the required information."}
            )
        attrs["buyer_info"] = buyer_info
        return attrs


class OrderReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderReport
        fields = ("title", "details")
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    amount_signed = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, source="signed_amount"
    )
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    product_name = serializers.CharField(read_only=True)
    package_name = serializers.CharField(read_only=True)
    group_name = serializers.CharField(read_only=True)
    detail = serializers.CharField(read_only=True)
    order_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "kind",
            "kind_label",
            "amount",
            "amount_signed",
            "balance_after",
            "method",
            "note",
            "product_name",
            "package_name",
            "group_name",
            "detail",
            "order_id",
            "created_at",
        )
        read_only_fields = (
            "id",
            "amount_signed",
            "kind_label",
            "balance_after",
            "product_name",
            "package_name",
            "group_name",
            "detail",
            "order_id",
            "created_at",
        )


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Staff-only: tops a customer's credit up."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Transaction
        fields = ("user", "kind", "amount", "method", "note")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Enter an amount greater than zero.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class CreditSerializer(serializers.ModelSerializer):
    """One credit row: a free-spend shortfall or an admin top-up."""

    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    order_name = serializers.SerializerMethodField()

    class Meta:
        model = Credit
        fields = (
            "id",
            "kind",
            "kind_label",
            "amount",
            "note",
            "order",
            "order_name",
            "created_at",
        )
        read_only_fields = fields

    def get_order_name(self, obj):
        if obj.order_id is None:
            return ""
        product = obj.order.package.product
        return f"{product.name} · {obj.order.package.name}"


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "The new password must be different."}
            )
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
