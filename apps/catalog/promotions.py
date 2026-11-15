"""Resolving which promotion applies to a product.

Kept outside the views so the checkout can price an order the same way the
storefront displays it.
"""

from .models import Promotion


def current_promotions(rows):
    """Map every product id to the promotion that applies to it.

    A product promotion wins over a category promotion. ``rows`` are dicts with
    ``id``, ``category_id`` and ``price_from``; the base prices are handed over
    so the calculation does not need extra queries.
    """
    prices = {
        row["id"]: row["price_from"]
        for row in rows
        if row.get("price_from") is not None
    }

    by_product = {}
    by_category = {}

    promotions = Promotion.objects.filter(is_active=True).select_related(
        "product", "category"
    )
    for promotion in promotions:
        if not promotion.is_current:
            continue
        if promotion.product_id:
            if promotion.product_id in prices:
                promotion._base_price = prices[promotion.product_id]
            by_product[promotion.product_id] = promotion
        elif promotion.category_id:
            by_category.setdefault(promotion.category_id, promotion)

    for row in rows:
        if row["id"] in by_product:
            continue
        promotion = by_category.get(row["category_id"])
        if promotion is None:
            continue
        promotion._base_price = prices.get(row["id"])
        by_product[row["id"]] = promotion

    return by_product


def promotion_price(product, price):
    """The price of ``price`` for ``product`` after the running promotion."""
    rows = [
        {
            "id": product.id,
            "category_id": product.category_id,
            "price_from": product.lowest_price,
        }
    ]
    promotion = current_promotions(rows).get(product.id)
    if promotion is None:
        return price
    return promotion.price_for(price)
