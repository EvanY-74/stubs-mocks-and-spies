import unittest
from unittest.mock import MagicMock
from report_generator import ReportGenerator
from interfaces import SaleRecord

class TestReportGenerator(unittest.TestCase):

    def test_empty_month_returns_zero_revenue(self):
        repo_stub = MagicMock()
        repo_stub.get_sales.return_value = []  # ← stub returns empty list

        gen    = ReportGenerator(repo_stub)
        result = gen.monthly_summary(1, 2024)

        self.assertEqual(result["total_revenue"], 0.0)
        self.assertIsNone(result["top_product"])

    def test_identifies_top_product_by_revenue(self):
        repo_stub = MagicMock()
        repo_stub.get_sales.return_value = [
            SaleRecord("SKU-A", 10, 500.00),
            SaleRecord("SKU-B", 3,  1200.00),  # ← highest
            SaleRecord("SKU-C", 20, 300.00),
        ]
        gen    = ReportGenerator(repo_stub)
        result = gen.monthly_summary(3, 2024)

        self.assertEqual(result["total_revenue"], 2000.00)
        self.assertEqual(result["top_product"],    "SKU-B")


    def test_single_product(self):
        repo_stub = MagicMock()
        total_revenue = 5000
        repo_stub.get_sales.return_value = [
            SaleRecord("SKU-D", 10, total_revenue),
        ]
        gen    = ReportGenerator(repo_stub)
        result = gen.monthly_summary(3, 2024)

        self.assertEqual(result["total_revenue"], total_revenue)
        self.assertEqual(result["top_product"],    "SKU-D")


    def test_tied_revenue(self):
        repo_stub = MagicMock()
        top_revenue = 5000
        repo_stub.get_sales.return_value = [
            SaleRecord("SKU-E", 10, top_revenue),
            SaleRecord("SKU-F", 10, top_revenue),
        ]
        gen    = ReportGenerator(repo_stub)
        result = gen.monthly_summary(3, 2024)

        self.assertIn(result["top_product"], ("SKU-E", "SKU-F"))


    def test_stub_simulates_repository_exception(self):
        repo_stub = MagicMock()
        repo_stub.get_sales.side_effect = ConnectionError("DB down")

        gen = ReportGenerator(repo_stub)
        with self.assertRaises(ConnectionError):
            gen.monthly_summary(6, 2024)