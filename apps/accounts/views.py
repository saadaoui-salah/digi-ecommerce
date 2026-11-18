from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.catalog.models import ItemType, PackageCode
from apps.catalog.promotions import promotion_price
from apps.catalog.services import claim_next_code
from apps.core.time import now as algeria_now

from .models import (
    Daira,
    Credit,
    CreditKind,
    Notification,
    NotificationKind,
    Order,
    OrderReport,
    OrderStatus,
    Transaction,
    TransactionKind,
    User,
    Wilaya,
)
from .serializers import (
    ChangePasswordSerializer,
    CreditSerializer,
    LoginSerializer,
    NotificationSerializer,
    OrderCreateSerializer,
    OrderReportCreateSerializer,
    OrderReportSerializer,
    OrderSerializer,
    OrderSoldSerializer,
    DairaSerializer,
    RegisterSerializer,
    WilayaOptionSerializer,
    ReferralProgramSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
    UserSerializer,
)
from .services import (
    InsufficientCredit,
    assign_order,
    change_status,
    coupon_for,
    create_order,
    notify,
)


def _cookie(response, name, value, max_age):
    jwt = settings.SIMPLE_JWT
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=jwt["AUTH_COOKIE_HTTP_ONLY"],
        secure=jwt["AUTH_COOKIE_SECURE"],
        samesite=jwt["AUTH_COOKIE_SAMESITE"],
        path=jwt["AUTH_COOKIE_PATH"],
    )


def set_auth_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    jwt = settings.SIMPLE_JWT
    _cookie(
        response,
        jwt["AUTH_COOKIE"],
        str(refresh.access_token),
        jwt["ACCESS_TOKEN_LIFETIME"].total_seconds(),
    )
    _cookie(
        response,
        jwt["AUTH_COOKIE_REFRESH"],
        str(refresh),
        jwt["REFRESH_TOKEN_LIFETIME"].total_seconds(),
    )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        set_auth_cookies(response, user)
        return response


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop("access", None)
        data.pop("refresh", None)
        response = Response(data)
        set_auth_cookies(response, serializer.user)
        return response


class CookieRefreshSerializer(TokenRefreshSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["refresh"].required = False

    def validate(self, attrs):
        if not attrs.get("refresh"):
            attrs["refresh"] = self.context["request"].COOKIES.get(
                settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"], ""
            )
        return super().validate(attrs)


class CookieRefreshView(TokenRefreshView):
    serializer_class = CookieRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc

        jwt = settings.SIMPLE_JWT
        response = Response({})
        _cookie(
            response,
            jwt["AUTH_COOKIE"],
            serializer.validated_data["access"],
            jwt["ACCESS_TOKEN_LIFETIME"].total_seconds(),
        )
        return response


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        jwt = settings.SIMPLE_JWT
        response = Response({"detail": "Logged out."})
        response.delete_cookie(jwt["AUTH_COOKIE"], path=jwt["AUTH_COOKIE_PATH"])
        response.delete_cookie(
            jwt["AUTH_COOKIE_REFRESH"], path=jwt["AUTH_COOKIE_PATH"]
        )
        return response


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class OrderListCreateView(generics.ListCreateAPIView):
    """The customer's own orders. Buying a package creates one.

    The list is searchable (`?search=`) and filterable by whether the customer
    recorded a resale price (`?sold=true|false`).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user).select_related(
            "code", "product", "package", "group"
        )

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search)
                | Q(package_name__icontains=search)
                | Q(group_name__icontains=search)
                | Q(category_name__icontains=search)
                | Q(id__icontains=search)
            )

        sold = self.request.query_params.get("sold")
        if sold in ("true", "false"):
            # ?sold=true → only orders with a resale price recorded.
            queryset = queryset.filter(sold_price__isnull=(sold == "false"))

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = serializer.validated_data["package_obj"]
        product = package.product

        is_instant = (
            product.type == ItemType.IMMEDIATE and package.type == ItemType.IMMEDIATE
        )

        # The whole checkout runs in one transaction and locks the customer
        # row, so two orders placed at the same moment cannot both spend the
        # same balance or claim the same code.
        try:
            with db_transaction.atomic():
                account = User.objects.select_for_update().get(pk=request.user.pk)
                price = promotion_price(product, package.price)
                # A coupon of the customer brings the price down.
                coupon = coupon_for(account, product)
                if coupon:
                    price = coupon.price_for(price)
                # Fast fail for customers without free spend; charge() repeats
                # the check under the lock before taking the money.
                if account.credit < price and not account.free_spend:
                    raise InsufficientCredit

                code = None
                if is_instant:
                    # The conditional UPDATE inside claim_next_code makes sure
                    # only one of two simultaneous customers can get a code.
                    code = claim_next_code(package, account)
                    if code is None:
                        return Response(
                            {"detail": "No codes are left for this package."},
                            status=status.HTTP_409_CONFLICT,
                        )

                order = create_order(
                    user=account,
                    package=package,
                    product=product,
                    group=package.group,
                    code=code,
                    price=price,
                    buyer_info=serializer.validated_data.get("buyer_info", ""),
                )

                # The coupon was used for that order.
                if coupon:
                    coupon.use()
        except InsufficientCredit:
            return Response(
                {"detail": "Not enough credit for this purchase."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderSummaryView(APIView):
    """Totals for the order history (all pages, not just the current one)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        totals = orders.aggregate(
            total_orders=Count("id"),
            total_spent=Coalesce(
                Sum("price", filter=Q(status__in=("processing", "delivered"))),
                Value(Decimal("0.00")),
            ),
            total_sold=Coalesce(
                Sum("sold_price"),
                Value(Decimal("0.00")),
            ),
            sold_count=Count("id", filter=Q(sold_price__isnull=False)),
        )
        return Response(
            {
                "total_orders": totals["total_orders"],
                "total_spent": f"{totals['total_spent']:.2f}",
                "total_sold": f"{totals['total_sold']:.2f}",
                "sold_count": totals["sold_count"],
            }
        )


class OrderSoldView(generics.UpdateAPIView):
    """Record (or clear) what the customer resold an order for."""

    serializer_class = OrderSoldSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ("patch",)

    def get_object(self):
        return get_object_or_404(
            Order, pk=self.kwargs["pk"], user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sold_price = serializer.validated_data["sold_price"]
        order.sold_price = sold_price
        order.sold_at = algeria_now() if sold_price is not None else None
        order.save(update_fields=["sold_price", "sold_at"])

        return Response(OrderSerializer(order).data)


class UserApprovalView(APIView):
    """Staff approves (or unapproves) a customer account."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can approve accounts.")

        account = get_object_or_404(User, pk=pk)
        action = request.data.get("action", "approve")

        if action == "approve":
            account.is_approved = True
            account.approved_at = algeria_now()
        elif action == "revoke":
            account.is_approved = False
            account.approved_at = None
        else:
            return Response(
                {"detail": "Unknown action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        account.save(update_fields=["is_approved", "approved_at"])
        if action == "approve":
            notify(
                account,
                NotificationKind.ACCOUNT_APPROVED,
                "Your account has been approved",
                "Your account is approved — you can now browse the catalog and place orders.",
            )
        return Response(UserSerializer(account).data)


class OrderTakeView(APIView):
    """An admin takes an on-demand order."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can take orders.")

        order = get_object_or_404(Order, pk=pk)
        if order.assigned_to_id and order.assigned_to_id != request.user.pk:
            return Response(
                {"detail": "This order is already taken by another admin."},
                status=status.HTTP_409_CONFLICT,
            )

        assign_order(order, request.user)
        return Response(OrderSerializer(order).data)


class OrderStatusView(APIView):
    """Staff moves an order to another status and the customer is notified."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can change an order status.")

        order = get_object_or_404(Order, pk=pk)
        new_status = request.data.get("status")
        if new_status not in OrderStatus.values:
            return Response(
                {"detail": "Unknown status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        report = None
        report_data = request.data.get("report")
        if isinstance(report_data, dict) and report_data.get("title"):
            report = OrderReport.objects.create(
                order=order,
                author=request.user,
                title=report_data["title"][:200],
                details=report_data.get("details", ""),
            )

        try:
            change_status(
                order,
                new_status,
                admin=request.user,
                report=report,
                note=request.data.get("note", ""),
            )
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(OrderSerializer(order).data)


class OrderReportListCreateView(generics.ListCreateAPIView):
    """The reports attached to an order."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        order = get_object_or_404(Order, pk=self.kwargs["order_id"])
        if self.request.user.is_staff or order.user_id == self.request.user.pk:
            return order.reports.select_related("author")
        return OrderReport.objects.none()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderReportCreateSerializer
        return OrderReportSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Only staff can write a report.")
        order = get_object_or_404(Order, pk=self.kwargs["order_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(order=order, author=request.user)
        return Response(
            OrderReportSerializer(report).data, status=status.HTTP_201_CREATED
        )


class NotificationListView(generics.ListAPIView):
    """The notifications of the signed-in user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get("unread") == "1":
            queryset = queryset.filter(is_read=False)
        return queryset

    def post(self, request):
        """Mark the notifications as read."""
        ids = request.data.get("ids")
        queryset = Notification.objects.filter(recipient=request.user, is_read=False)
        if isinstance(ids, list) and ids:
            queryset = queryset.filter(id__in=ids)
        queryset.update(is_read=True)
        return Response({"updated": queryset.count()})


class TransactionListCreateView(generics.ListCreateAPIView):
    """The customer's own credit history. Staff can create top-ups."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.select_related("user")
        if self.request.user.is_staff and self.request.query_params.get("all") == "1":
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            if not self.request.user.is_staff:
                raise PermissionDenied("Only staff can create transactions.")
            return TransactionCreateSerializer
        return TransactionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        return Response(
            TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED
        )


class TransactionSummaryView(APIView):
    """Credit totals for the signed-in customer."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        totals = transactions.aggregate(
            credited=Coalesce(
                Sum("amount", filter=Q(kind__in=("credit", "refund"))),
                Value(Decimal("0.00")),
            ),
            debited=Coalesce(
                Sum("amount", filter=Q(kind="order")),
                Value(Decimal("0.00")),
            ),
        )
        return Response(
            {
                "total_credited": f"{totals['credited']:.2f}",
                "total_debited": f"{totals['debited']:.2f}",
                "credit_balance": f"{request.user.credit:.2f}",
            }
        )


class CreditListView(APIView):
    """The signed-in customer's credit rows plus the running totals.

    A `debt` row is what a free-spend customer owes after buying with an
    empty balance; a `topup` row is an amount an admin granted them.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        credits = Credit.objects.filter(user=request.user).select_related(
            "order", "order__package", "order__package__product"
        )
        totals = credits.aggregate(
            owed=Coalesce(
                Sum("amount", filter=Q(kind=CreditKind.DEBT)),
                Value(Decimal("0.00")),
            ),
            granted=Coalesce(
                Sum("amount", filter=Q(kind=CreditKind.TOPUP)),
                Value(Decimal("0.00")),
            ),
        )
        return Response(
            {
                "balance": f"{request.user.credit:.2f}",
                "free_spend": request.user.free_spend,
                "total_owed": f"{totals['owed']:.2f}",
                "total_granted": f"{totals['granted']:.2f}",
                "results": CreditSerializer(credits, many=True).data,
            }
        )


class WilayaListView(APIView):
    """All active wilayas. Regions are admin-only and never exposed here."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        wilayas = Wilaya.objects.filter(is_active=True).order_by("name")
        return Response(WilayaOptionSerializer(wilayas, many=True).data)


class DairaListView(APIView):
    """The dairas of one wilaya, fetched when the visitor picks it."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        wilaya_id = request.query_params.get("wilaya")
        if not wilaya_id or not str(wilaya_id).isdigit():
            return Response({"detail": "A valid wilaya id is required."}, status=400)
        dairas = Daira.objects.filter(
            is_active=True, wilaya_id=int(wilaya_id), wilaya__is_active=True
        ).order_by("name")
        return Response(DairaSerializer(dairas, many=True).data)


class ReferralProgramView(APIView):
    """The referral program of the signed-in customer.

    It holds their link — the code that goes in the query string — and the
    table of what they earned from the customers they referred.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = ReferralProgramSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response(
            {"detail": "Password updated.", "user": UserSerializer(user).data}
        )
        # Refresh the session cookies so the current client stays in sync.
        set_auth_cookies(response, user)
        return response
