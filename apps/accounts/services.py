"""Order workflow helpers.

Instant orders are delivered straight away. On-demand orders are picked up by
an admin, worked on, and every status change notifies the customer.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from django.utils import timezone

from apps.core.time import now as algeria_now

from .models import (
    Coupon,
    Credit,
    CreditKind,
    Notification,
    NotificationKind,
    Order,
    OrderStatus,
    Referral,
    Transaction,
    TransactionKind,
)

User = get_user_model()


class InsufficientCredit(Exception):
    """The balance cannot cover the price and the customer has no free spend."""


def coupon_for(user, product):
    """The coupon of a customer that applies to a product, if there is one.

    The coupon that is used is the one that was made for them last, so the
    newest discount is the one they see.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    return (
        Coupon.objects.filter(user=user, product=product, is_active=True)
        .order_by("-created_at", "-id")
        .first()
    )


def pay_referral(order):
    """Pay the customer who referred the buyer of an order.

    They earn a percentage of the order. What they owe is paid down first;
    what is left goes to their balance. The earning is recorded as a
    transaction and as a credit row of its own type.
    """
    referrer = order.user.referred_by
    if referrer is None:
        return None

    if not referrer.accepts_referrals:
        return None

    percentage = Decimal(referrer.referral_percentage or 0)
    if percentage <= 0:
        return None

    amount = (Decimal(order.price) * percentage / Decimal("100")).quantize(
        Decimal("0.01")
    )
    if amount <= 0:
        return None

    remaining = amount

    # What the referrer owes is paid down first.
    for debt in Credit.objects.filter(
        user=referrer, kind=CreditKind.DEBT
    ).order_by("created_at", "id"):
        if remaining <= 0:
            break

        paid = min(debt.amount, remaining)
        debt.amount -= paid
        remaining -= paid

        if debt.amount <= 0:
            debt.delete()
        else:
            debt.save(update_fields=["amount"])

    # What is left goes to the balance.
    if remaining > 0:
        Transaction.objects.create(
            user=referrer,
            kind=TransactionKind.REFERRAL,
            amount=remaining,
            method="Referral",
            note=f"Referral from {order.user}",
            order=order,
        )

    # The whole earning is recorded with its own type.
    Credit.objects.create(
        user=referrer,
        kind=CreditKind.REFERRAL,
        amount=amount,
        order=order,
        note=f"Referral from {order.user}",
    )

    referral = Referral.objects.create(
        referrer=referrer,
        referred=order.user,
        order=order,
        amount=amount,
        percentage=percentage,
    )

    notify(
        referrer,
        NotificationKind.REFERRAL,
        "You earned a referral bonus",
        (
            f"{order.user} placed an order — you earned {amount:.2f} DA for "
            "bringing them in."
        ),
        order=order,
    )

    return referral


def notify(recipient, kind, title, body="", order=None):
    """Create one notification for a user."""
    return Notification.objects.create(
        recipient=recipient,
        kind=kind,
        title=title,
        body=body,
        order=order,
    )


def notify_admins(kind, title, body="", order=None, exclude=None):
    """Notify every admin that can take on-demand work."""
    admins = User.objects.filter(is_staff=True)
    if exclude is not None:
        admins = admins.exclude(pk=exclude.pk)

    return [
        notify(admin, kind, title, body, order) for admin in admins
    ]


@db_transaction.atomic
def charge(user, order, price):
    """Take the payment for an order, under a lock on the customer row.

    The row lock is what keeps two simultaneous orders from both spending the
    same balance: the second one waits here until the first commits.

    A customer with free spend pays whatever is left on the balance and owes
    the remainder as a `Credit` row — so the balance itself never drops below
    zero. Everyone else must have the full price available.
    """
    price = Decimal(price)
    account = User.objects.select_for_update().get(pk=user.pk)
    balance = Decimal(account.credit)

    if balance >= price:
        Transaction.objects.create(
            user=account,
            kind=TransactionKind.ORDER,
            amount=price,
            method="Purchase",
            note=f"Order {order.pk}",
            order=order,
        )
    elif account.free_spend:
        # Pay down what is there first, then record the shortfall.
        if balance > 0:
            Transaction.objects.create(
                user=account,
                kind=TransactionKind.ORDER,
                amount=balance,
                method="Purchase",
                note=f"Order {order.pk}",
                order=order,
            )
        shortfall = price - balance
        Credit.objects.create(
            user=account,
            kind=CreditKind.DEBT,
            amount=shortfall,
            order=order,
            note=f"Order {order.pk}",
        )
        # The balance never goes negative; free-spend purchases accumulate on
        # the user's own "owed" field instead.
        account.owed += shortfall
        account.save(update_fields=["owed"])
    else:
        raise InsufficientCredit("Not enough credit for this purchase.")

    account.refresh_from_db()
    user.credit = account.credit
    return account.credit


@db_transaction.atomic
def create_order(
    *, user, package, product, group=None, code=None, price=None,
    quantity=1, buyer_info=""
):
    """Create an order, charge the credit and notify the right people.

    ``price`` is the amount actually charged — it defaults to the package price
    but checkout passes the promoted price when a promotion is running.
    ``buyer_info`` holds whatever the buyer typed in the pre-order popup.
    """
    is_instant = package.type == "immediate"
    if price is None:
        price = package.price

    order = Order.objects.create(
        user=user,
        product=product,
        package=package,
        group=group,
        code=code,
        product_name=product.name,
        product_slug=product.slug,
        category_name=product.category.name if product.category_id else "",
        package_name=package.name,
        group_name=group.name if group else "",
        price=price,
        quantity=quantity,
        cost=package.cost,
        buyer_info=buyer_info,
        status=OrderStatus.DELIVERED if is_instant else OrderStatus.PENDING,
    )

    charge(user, order, Decimal(price) * quantity)

    if is_instant:
        notify(
            user,
            NotificationKind.ORDER_DELIVERED,
            "Your order is ready",
            f"{product.name} — your code is available in the orders page.",
            order=order,
        )
    else:
        notify_admins(
            NotificationKind.ORDER_PLACED,
            f"New on-demand order #{order.pk}",
            f"{user} ordered {product.name} ({package.name}).",
            order=order,
        )
        notify(
            user,
            NotificationKind.ORDER_PLACED,
            "We received your order",
            f"An admin will start working on {product.name} shortly.",
            order=order,
        )

    return order


@db_transaction.atomic
def assign_order(order, admin):
    """An admin takes the order: it is theirs and the work starts."""
    order.assigned_to = admin
    order.assigned_at = algeria_now()
    if order.status in (OrderStatus.PENDING, OrderStatus.HAS_PROBLEMS):
        order.status = OrderStatus.IN_PROGRESS
    order.save(update_fields=["assigned_to", "assigned_at", "status"])

    notify(
        order.user,
        NotificationKind.ORDER_ASSIGNED,
        "An admin is working on your order",
        f"{admin.get_full_name() or admin.username} took over order #{order.pk}.",
        order=order,
    )

    # The other admins no longer need to act on this order.
    Notification.objects.filter(
        order=order, recipient__is_staff=True, is_read=False
    ).exclude(recipient=admin).update(is_read=True)

    return order


@db_transaction.atomic
def change_status(order, status, admin=None, report=None, note=""):
    """Move an order to another status and notify the customer."""
    status = OrderStatus(status)

    if status == OrderStatus.HAS_PROBLEMS and report is None:
        # A problem needs a note: the staff write down what went wrong.
        if not order.reports.exists():
            raise ValueError("A report is required to flag a problem.")

    previous = order.status
    order.status = status
    fields = ["status"]
    if status == OrderStatus.DELIVERED and order.assigned_to is None and admin:
        order.assigned_to = admin
        fields.append("assigned_to")
    order.save(update_fields=fields)

    titles = {
        OrderStatus.PENDING: "Your order is waiting for an admin",
        OrderStatus.IN_PROGRESS: "Your order is in progress",
        OrderStatus.HAS_PROBLEMS: "Your order has a problem",
        OrderStatus.DELIVERED: "Your order was delivered",
        OrderStatus.REFUNDED: "Your order was refunded",
        OrderStatus.CANCELLED: "Your order was cancelled",
    }

    def label(value):
        return dict(OrderStatus.choices).get(value, value)

    notify(
        order.user,
        NotificationKind.STATUS_CHANGED,
        titles.get(status, "Your order was updated"),
        note
        or f"Order #{order.pk} moved from {label(previous)} to {label(status)}.",
        order=order,
    )

    if status == OrderStatus.DELIVERED:
        notify(
            order.user,
            NotificationKind.ORDER_DELIVERED,
            "Your order is ready",
            f"{order.product_name} — your code is available in the orders page.",
            order=order,
        )

    return order
