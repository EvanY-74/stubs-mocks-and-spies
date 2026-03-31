import unittest
from unittest.mock import MagicMock

# ── Production code ─────────────────────────────────────────
class TaxCalculator:
    RATE = 0.20
    def compute(self, amount: float) -> float:
        return round(amount * self.RATE, 2)

class InvoiceService:
    def __init__(self, tax_calc: TaxCalculator):
        self._tax = tax_calc

    def generate(self, subtotal: float) -> dict:
        tax   = self._tax.compute(subtotal)
        total = subtotal + tax
        return {"subtotal": subtotal, "tax": tax, "total": total}

# ── Tests using a spy ───────────────────────────────────────
class TestInvoiceServiceWithSpy(unittest.TestCase):

    def setUp(self):
        real_calc    = TaxCalculator()
        self.spy_calc = MagicMock(wraps=real_calc)  # ← spy wraps real
        self.svc     = InvoiceService(self.spy_calc)

    def test_invoice_computes_correct_total(self):
        """Real TaxCalculator logic runs — result is trustworthy."""
        invoice = self.svc.generate(500.00)

        self.assertEqual(invoice["tax"],   100.00)   # 20% of 500
        self.assertEqual(invoice["total"], 600.00)

    def test_tax_calculator_called_with_subtotal(self):
        """Spy verifies delegation: correct amount forwarded."""
        self.svc.generate(250.00)

        self.spy_calc.compute.assert_called_once_with(250.00)

    def test_tax_calculator_called_exactly_once_per_invoice(self):
        """Spy counts calls — no accidental double-computation."""
        self.svc.generate(100.00)

        self.assertEqual(self.spy_calc.compute.call_count, 1)

    def test_spy_captures_return_value(self):
        """Inspect the real return value directly from the call result."""
        # In unittest.mock, the spy returns the real value directly.
        # Capture it as the return value of the call — no special attribute needed.
        tax_value = self.spy_calc.compute(1000.00)   # real method called
        self.assertEqual(tax_value, 200.00)   # 20% of 1000

# ── Contrast: same tests with a mock (no real logic) ────────
class TestInvoiceServiceWithMock(unittest.TestCase):

    def setUp(self):
        self.mock_calc = MagicMock()                  # ← pure mock
        self.mock_calc.compute.return_value = 50.00    # ← canned value
        self.svc = InvoiceService(self.mock_calc)

    def test_total_uses_tax_from_calculator(self):
        """Mock controls input — test only InvoiceService logic."""
        invoice = self.svc.generate(200.00)

        # Tax is whatever the mock returned (50), not real 20%
        self.assertEqual(invoice["total"], 250.00)
        self.mock_calc.compute.assert_called_once_with(200.00)