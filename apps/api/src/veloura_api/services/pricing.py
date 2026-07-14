from decimal import ROUND_HALF_UP, Decimal

FREE_SHIPPING_THRESHOLD = Decimal("100.00")
STANDARD_SHIPPING = Decimal("7.99")
TAX_RATE = Decimal("0.0825")


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_order_totals(subtotal: float) -> dict:
    """Simple, documented pricing rule: free shipping over $100, otherwise a flat
    $7.99 rate, plus 8.25% sales tax applied to the subtotal."""
    subtotal_d = Decimal(str(subtotal))
    shipping = Decimal("0.00") if subtotal_d >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING
    tax = subtotal_d * TAX_RATE
    total = subtotal_d + shipping + tax
    return {
        "subtotal": _round(subtotal_d),
        "shipping_cost": _round(shipping),
        "tax": _round(tax),
        "total": _round(total),
    }
