"""Reactions to model saves.

A `Credit` row created by staff (a top-up) tops the customer's balance up and
tells them about it. Order-side rows are always `debt` — they record what a
free-spend customer owes — so the signal never fires for them.

The order signals keep the counters of the customer up to date, so the
dashboard reads them instead of walking the orders. Every figure of the shop
is a counter like that one, moved by a signal:

* the revenue, the profit, the margin, the benefits and the order counts of
  a customer, of a product, of a category and of a package;
* the worth of the stock the shop has not sold yet, kept on the staff
  accounts (the code signals of the catalog move it).
"""

from decimal import Decimal

from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.catalog.models import Category, Package, Product
from apps.catalog.services import unsold_stock_quantity, unsold_stock_worth
from apps.core.money import percentage as profit_percentage

from .models import (
    Credit,
    CreditKind,
    Notification,
    NotificationKind,
    Order,
    OrderStatus,
    User,
)
from .services import pay_referral

#: The on-demand statuses that still wait for the customer.
PENDING_DEMAND_STATUSES = (
    OrderStatus.PENDING,
    OrderStatus.IN_PROGRESS,
    OrderStatus.HAS_PROBLEMS,
)


@receiver(post_save, sender=Credit)
def apply_credit_topup(sender, instance, created, **kwargs):
    """Add a staff-granted top-up to the customer's balance, once."""
    if not created or instance.kind != CreditKind.TOPUP:
        return

    with transaction.atomic():
        account = User.objects.select_for_update().get(pk=instance.user_id)
        balance = Decimal(account.credit) + Decimal(instance.amount)
        account.credit = balance
        account.save(update_fields=["credit"])

        # The customer hears about the credit the moment it is granted.
        Notification.objects.create(
            recipient=account,
            kind=NotificationKind.CREDIT_TOPUP,
            title="Credit added to your account",
            body=(
                f"{Decimal(instance.amount):.2f} DA was added to your balance. "
                f"Your new balance is {balance:.2f} DA."
            ),
        )


@receiver(post_save, sender=User)
def seed_staff_stock_worth(sender, instance, created, **kwargs):
    """Give a new staff account the figures of the unsold stock.

    The worth and the quantity are figures of the shop, so every staff
    account carries them. A staff member created after the codes were added
    reads them from the packages, so no account ever starts with a wrong
    number.
    """
    if not created or not instance.is_staff:
        return

    worth = unsold_stock_worth()
    quantity = unsold_stock_quantity()
    if not worth and not quantity:
        return

    instance.stock_worth = worth
    instance.stock_quantity = quantity
    instance.save(update_fields=["stock_worth", "stock_quantity"])


def _benefit_of(order) -> Decimal:
    """What the customer earned by reselling the order."""
    if order.sold_price is None:
        return Decimal("0.00")
    return Decimal(order.sold_price) - Decimal(order.price)


def _profit_of(order) -> Decimal:
    """What the store earned on the order: the price minus what it cost."""
    return Decimal(order.price) - Decimal(order.cost)


def _pending_for(status, product_id) -> int:
    """Whether an order with this status and product waits for the customer."""
    if status not in PENDING_DEMAND_STATUSES:
        return 0
    if product_id is None:
        return 1
    product = Product.objects.filter(pk=product_id).only("type").first()
    if product is not None and product.type == "immediate":
        return 0
    return 1


def _apply_counters(user_id, *, revenue, profit, benefit, orders, pending):
    """Move the counters of a customer by the given amounts."""
    if not (revenue or profit or benefit or orders or pending):
        return

    with transaction.atomic():
        account = User.objects.select_for_update().get(pk=user_id)
        account.total_revenue = max(
            Decimal("0.00"), Decimal(account.total_revenue) + Decimal(revenue)
        )
        account.net_profit = max(
            Decimal("0.00"), Decimal(account.net_profit) + Decimal(profit)
        )
        account.total_benefit = max(
            Decimal("0.00"), Decimal(account.total_benefit) + Decimal(benefit)
        )
        account.orders_count = max(0, account.orders_count + int(orders))
        account.pending_demand_orders = max(
            0, account.pending_demand_orders + int(pending)
        )
        # The percentage follows the two figures it is made of, so the page
        # never has to divide anything.
        account.net_profit_percentage = profit_percentage(
            account.net_profit, account.total_revenue
        )
        account.save(
            update_fields=[
                "total_revenue",
                "net_profit",
                "total_benefit",
                "orders_count",
                "pending_demand_orders",
                "net_profit_percentage",
            ]
        )


def _move_catalog_counters(
    order, *, revenue, profit, benefit, orders, pending
):
    """Move the counters of the product, its category and its package.

    The figures of the analytics page are read from the catalog rows, so the
    counters there have to move with the orders.
    """
    if not (revenue or profit or benefit or orders or pending):
        return

    targets = []
    if order.product_id is not None:
        targets.append(Product.objects.filter(pk=order.product_id).first())
    if order.package_id is not None:
        targets.append(Package.objects.filter(pk=order.package_id).first())

    for target in targets:
        if target is None:
            continue
        target.sales_count = max(0, target.sales_count + int(orders))
        target.total_revenue = max(
            Decimal("0.00"), Decimal(target.total_revenue) + Decimal(revenue)
        )
        target.net_profit = max(
            Decimal("0.00"), Decimal(target.net_profit) + Decimal(profit)
        )
        target.total_benefit = max(
            Decimal("0.00"), Decimal(target.total_benefit) + Decimal(benefit)
        )
        if hasattr(target, "pending_demand_orders"):
            target.pending_demand_orders = max(
                0, target.pending_demand_orders + int(pending)
            )
        target.save(
            update_fields=[
                "sales_count",
                "total_revenue",
                "net_profit",
                "total_benefit",
            ]
            + (["pending_demand_orders"] if hasattr(target, "pending_demand_orders") else [])
        )

    # The category of the product gets the same figures.
    category = None
    if order.product_id is not None:
        category = Category.objects.filter(
            pk=Product.objects.filter(pk=order.product_id).values_list(
                "category_id", flat=True
            ).first()
        ).first()
    if category is None:
        return

    category.sales_count = max(0, category.sales_count + int(orders))
    category.total_revenue = max(
        Decimal("0.00"), Decimal(category.total_revenue) + Decimal(revenue)
    )
    category.net_profit = max(
        Decimal("0.00"), Decimal(category.net_profit) + Decimal(profit)
    )
    category.total_benefit = max(
        Decimal("0.00"), Decimal(category.total_benefit) + Decimal(benefit)
    )
    category.pending_demand_orders = max(
        0, category.pending_demand_orders + int(pending)
    )
    category.save(
        update_fields=[
            "sales_count",
            "total_revenue",
            "net_profit",
            "total_benefit",
            "pending_demand_orders",
        ]
    )


@receiver(pre_save, sender=Order)
def remember_order_before_save(sender, instance, **kwargs):
    """Stash the values of the order before it changes.

    The signal that moves the counters runs after the save, so it needs to
    know what the row looked like before.
    """
    if not instance.pk:
        instance._previous_values = (Decimal("0.00"), None, "", None, Decimal("0.00"))
        return

    stored = (
        Order.objects.filter(pk=instance.pk)
        .values_list("price", "sold_price", "status", "product_id", "cost")
        .first()
    ) or (Decimal("0.00"), None, "", None, Decimal("0.00"))
    instance._previous_values = stored


@receiver(post_save, sender=Order)
def track_order_counters(sender, instance, created, **kwargs):
    """Keep the counters of the customer in step with their orders."""
    old_price, old_sold, old_status, old_product, old_cost = getattr(
        instance, "_previous_values", (Decimal("0.00"), None, "", None, Decimal("0.00"))
    )

    old_benefit = (
        Decimal("0.00") if old_sold is None else Decimal(old_sold) - Decimal(old_price)
    )
    old_profit = Decimal(old_price) - Decimal(old_cost)

    if created:
        revenue = Decimal(instance.price)
        profit = _profit_of(instance)
        benefit = _benefit_of(instance)
        orders = 1
        pending = _pending_for(instance.status, instance.product_id)
    else:
        revenue = Decimal(instance.price) - Decimal(old_price)
        profit = _profit_of(instance) - old_profit
        benefit = _benefit_of(instance) - old_benefit
        orders = 0

        # A demand order stops waiting once it is delivered or cancelled.
        pending = _pending_for(
            instance.status, instance.product_id
        ) - _pending_for(old_status, old_product)

    _apply_counters(
        instance.user_id,
        revenue=revenue,
        profit=profit,
        benefit=benefit,
        orders=orders,
        pending=pending,
    )
    _move_catalog_counters(
        instance,
        revenue=revenue,
        profit=profit,
        benefit=benefit,
        orders=orders,
        pending=pending,
    )


@receiver(post_save, sender=Order)
def pay_order_referral(sender, instance, created, **kwargs):
    """Pay the customer who referred the buyer of a new order."""
    if not created:
        return

    pay_referral(instance)


@receiver(post_delete, sender=Order)
def forget_order_counters(sender, instance, **kwargs):
    """Take a deleted order back out of the counters."""
    _apply_counters(
        instance.user_id,
        revenue=-Decimal(instance.price),
        profit=-_profit_of(instance),
        benefit=-_benefit_of(instance),
        orders=-1,
        pending=-_pending_for(instance.status, instance.product_id),
    )
    _move_catalog_counters(
        instance,
        revenue=-Decimal(instance.price),
        profit=-_profit_of(instance),
        benefit=-_benefit_of(instance),
        orders=-1,
        pending=-_pending_for(instance.status, instance.product_id),
    )
