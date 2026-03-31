# ── report_generator.py ─────────────────────────────────────
class ReportGenerator:
    def __init__(self, repo: SalesRepository):
        self._repo = repo

    def monthly_summary(self, month: int, year: int) -> dict:
        records = self._repo.get_sales(month, year)
        if not records:
            return {"total_revenue": 0.0, "top_product": None}
        total = sum(r.revenue for r in records)
        top   = max(records, key=lambda r: r.revenue)
        return {
            "total_revenue": round(total, 2),
            "top_product":   top.product_id,
        }