import type { Coupon } from "@/lib/api";

/**
 * The price the customer pays for a package with a coupon.
 *
 * It is the same rule the backend uses when the order is placed, so the
 * price on the page is the price that is charged.
 */
export function couponPrice(coupon: Coupon | null, price: number): number {
  if (!coupon) return price;

  if (coupon.percentage) {
    return round(price * (1 - Number(coupon.percentage) / 100));
  }

  if (coupon.discount_price) {
    return Math.min(price, Number(coupon.discount_price));
  }

  return price;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}
