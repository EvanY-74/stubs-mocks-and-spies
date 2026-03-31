from unittest.mock import MagicMock

# ── The real object we want to observe ───────────────────────
# TaxCalculator is a pure class: no network, no disk, no side-effects.
# It's safe to run in tests — so instead of replacing it with a mock
# (which would hide whether the formula is correct), we use a spy
# that lets the real logic run while we observe the calls.
class TaxCalculator:
    RATE = 0.20  # 20% tax rate

    def compute(self, amount: float) -> float:
        return round(amount * self.RATE, 2)

    def compute_with_discount(self, amount: float, discount: float) -> float:
        discounted = amount * (1 - discount)
        # Delegates to compute() internally — useful for testing delegation
        return self.compute(discounted)

# ── Create a spy that wraps the real instance ─────────────────
# wraps=real_calc means:
#   • Any method call on spy_calc is forwarded to real_calc
#   • The real code executes and returns a real value
#   • Additionally, the call is recorded on spy_calc for assertions
real_calc = TaxCalculator()
spy_calc  = MagicMock(wraps=real_calc)   # spy wraps the real instance

# ── Calling through the spy ───────────────────────────────────
# The spy forwards this call to real_calc.compute(100.0).
# The real code runs and the return value (20.0) comes back directly.
result = spy_calc.compute(100.0)
print(result)   # 20.0 — real logic ran, returned directly

# ── Spy records the call just like a mock ─────────────────────
# Even though the real code ran, the spy still recorded the call.
spy_calc.compute.assert_called_once_with(100.0)
print(spy_calc.compute.call_count)   # 1 — one call so far

# ── Observing internal delegation ────────────────────────────
# compute_with_discount() calls compute() internally.
# The spy records BOTH the outer call and the inner delegation.
spy_calc.compute_with_discount(200.0, 0.1)
print(spy_calc.compute.call_count)   # 2 — compute() was called again internally

# ── Capturing the real return value ──────────────────────────
# In unittest.mock, the spy returns the real value directly.
# Capture it from the call result — no special attribute needed.
real_result = spy_calc.compute(500.0)   # real_result = 100.0
print(real_result)   # 100.0 — the real method's return value