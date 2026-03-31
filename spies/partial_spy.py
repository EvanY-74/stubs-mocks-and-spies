from unittest.mock import patch
import unittest

class PricingEngine:
    def base_price(self, product_id: str) -> float:
        # In production this might query a pricing database.
        # Here it's a simple dict lookup for illustration.
        return {"A": 9.99, "B": 14.99}.get(product_id, 0.0)

    def final_price(self, product_id: str, qty: int) -> float:
        # final_price delegates to base_price internally.
        # We want to verify this delegation without replacing the engine.
        bp = self.base_price(product_id)
        return round(bp * qty, 2)

class TestPricingEnginePartialSpy(unittest.TestCase):

    def test_final_price_delegates_to_base_price(self):
        engine = PricingEngine()

        # patch.object with wraps= creates a PARTIAL spy:
        #   - Only base_price is observed; everything else is untouched
        #   - wraps=engine.base_price means the real method still runs
        #   - The spy is only active inside this `with` block; it is
        #     automatically removed when the block exits
        with patch.object(
            engine, "base_price",
            wraps=engine.base_price  # real method forwarded
        ) as spy:
            result = engine.final_price("A", 3)

        # Real formula ran: 9.99 * 3 = 29.97
        self.assertEqual(result, 29.97)
        # Delegation verified: final_price called base_price with "A"
        spy.assert_called_once_with("A")

    def test_base_price_called_once_not_twice(self):
        # Guard: final_price must call base_price exactly once.
        # If it accidentally called it twice, we'd compute the wrong total.
        engine = PricingEngine()
        with patch.object(engine, "base_price", wraps=engine.base_price) as spy:
            engine.final_price("B", 2)
        self.assertEqual(spy.call_count, 1)