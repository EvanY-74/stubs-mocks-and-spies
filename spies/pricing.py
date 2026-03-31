from dataclasses import dataclass

@dataclass
class Product:
    sku:        str
    base_price: float
    category:   str    # "electronics", "clothing", "food"

class PriceCalculator:
    CATEGORY_RATES = {"electronics": 0.10, "clothing": 0.20, "food": 0.05}

    def discount(self, product: Product, pct: float) -> float:
        """Apply percentage discount. Returns discounted price."""
        return round(product.base_price * (1 - pct), 2)

    def category_tax(self, product: Product) -> float:
        """Returns tax amount based on product category."""
        rate = self.CATEGORY_RATES.get(product.category, 0.15)
        return round(product.base_price * rate, 2)

class DiscountEngine:
    """Applies promotions using the PriceCalculator."""

    def __init__(self, calc: PriceCalculator):
        self._calc = calc

    def apply_sale(self, product: Product, sale_pct: float) -> dict:
        """Discounts a product and computes final price with tax."""
        discounted = self._calc.discount(product, sale_pct)
        tax        = self._calc.category_tax(product)
        return {
            "sku":        product.sku,
            "discounted": discounted,
            "tax":        tax,
            "total":      round(discounted + tax, 2),
        }