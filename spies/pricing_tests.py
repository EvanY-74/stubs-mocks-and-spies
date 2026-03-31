import unittest
from unittest.mock import MagicMock
from pricing import Product, PriceCalculator, DiscountEngine

class TestDiscountEngine(unittest.TestCase):

    def setUp(self):
        real_calc      = PriceCalculator()
        self.spy_calc  = MagicMock(wraps=real_calc)  # spy
        self.engine    = DiscountEngine(self.spy_calc)

        self.laptop = Product("LAP-01", 1000.00, "electronics")
        self.shirt  = Product("SHT-99", 50.00, "clothing")

    def test_apply_sale_returns_correct_totals(self):
        # Real PriceCalculator runs — results are trustworthy
        result = self.engine.apply_sale(self.laptop, 0.10)  # 10% off

        self.assertEqual(result["discounted"], 900.00)  # 1000 * 0.9
        self.assertEqual(result["tax"],        100.00)  # 1000 * 10%
        self.assertEqual(result["total"],      1000.00) # 900 + 100

    def test_discount_called_with_correct_product_and_pct(self):
        # Spy verifies delegation arguments
        self.engine.apply_sale(self.shirt, 0.25)

        self.spy_calc.discount.assert_called_once_with(self.shirt, 0.25)

    def test_category_tax_called_with_correct_product(self):
        self.engine.apply_sale(self.laptop, 0.05)

        self.spy_calc.category_tax.assert_called_once_with(self.laptop)

    def test_both_calculator_methods_called_once_per_sale(self):
        # Guard against accidental double-calls
        self.engine.apply_sale(self.shirt, 0.10)

        self.assertEqual(self.spy_calc.discount.call_count,     1)
        self.assertEqual(self.spy_calc.category_tax.call_count, 1)

    def test_real_return_value_flows_into_result_dict(self):
        # In unittest.mock, the spy returns the real value directly.
        # Capture the result of apply_sale() — it contains the real computed values.
        # This confirms both: the formula is correct AND DiscountEngine
        # stored the value in the dict without any transformation.
        result = self.engine.apply_sale(self.laptop, 0.20)

        # Real formula: 1000 * (1 - 0.20) = 800.00
        self.assertEqual(result["discounted"], 800.00)  # 1000 * 0.8
        self.assertEqual(result["tax"],        100.00)  # 1000 * 10%
        
    def test_apply_sale(self):
        self.engine.apply_sale(self.laptop, .1)
        self.engine.apply_sale(Product("LAP-02", 1200, "electronics"), .2)
        self.engine.apply_sale(self.shirt, .2)

        self.assertEqual(self.spy_calc.discount.call_count, 3)
    
    def test_partial_spy(self):
        self.engine.apply_sale(self.shirt, 0.2)

        self.spy_calc.discount.assert_called_once_with(self.shirt, 0.2)