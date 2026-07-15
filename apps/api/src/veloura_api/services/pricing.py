from decimal import ROUND_HALF_UP, Decimal

FREE_SHIPPING_THRESHOLD = Decimal("100.00")
STANDARD_SHIPPING = Decimal("7.99")
TAX_RATE = Decimal("0.0825")


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_order_totals(
    subtotal: float, *, discount_amount: float = 0.0, free_shipping: bool = False
) -> dict:
    """Simple, documented pricing rule: free shipping over $100 (or via an
    applied coupon), otherwise a flat $7.99 rate, plus 8.25% sales tax applied
    to the discounted subtotal. Coupon discounts are always computed and
    applied server-side - the frontend only ever displays what this returns."""
    subtotal_d = Decimal(str(subtotal))
    discount_d = min(Decimal(str(discount_amount)), subtotal_d)
    discounted_subtotal = subtotal_d - discount_d

    qualifies_free_shipping = free_shipping or discounted_subtotal >= FREE_SHIPPING_THRESHOLD
    shipping = Decimal("0.00") if qualifies_free_shipping else STANDARD_SHIPPING
    tax = discounted_subtotal * TAX_RATE
    total = discounted_subtotal + shipping + tax
    return {
        "subtotal": _round(subtotal_d),
        "discount_amount": _round(discount_d),
        "shipping_cost": _round(shipping),
        "tax": _round(tax),
        "total": _round(total),
    }


def free_shipping_remaining(subtotal: float, discount_amount: float = 0.0) -> float:
    discounted = Decimal(str(subtotal)) - Decimal(str(discount_amount))
    remaining = FREE_SHIPPING_THRESHOLD - discounted
    return _round(remaining) if remaining > 0 else 0.0
