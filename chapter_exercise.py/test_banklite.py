import unittest
from unittest.mock import MagicMock
from banklite import *

class TestDiscountEngine(unittest.TestCase):

    def setUp(self):
        self.gateway = MagicMock()
        self.audit   = MagicMock()
        self.proc    = PaymentProcessor(self.gateway, self.audit)

        # self.gateway.charge.return_value = True

        # self.gateway.charge.assert_not_called()

        # # tx = Transaction.tx_id

        # self.audit.record.assert_called_once_with(
        #     "CHARGED", tx.tx_id, {"amount": tx.amount}
        # )


    def _make_tx(self, amount=100.00, tx_id="TX-001", user_id=1):
        """Helper: build a Transaction. Keeps test setup DRY.
        Default values mean each test only specifies what it cares about."""

        return Transaction(tx_id=tx_id, user_id=user_id, amount=amount)


    def test_process_returns_success_when_gateway_charges(self):
        self.gateway.charge.return_value = True
        self.assertEqual(self.proc.process(self._make_tx()), "success")

    def test_process_returns_declined_when_gateway_rejects(self):
        self.gateway.charge.return_value = False
        self.assertEqual(self.proc.process(self._make_tx()), "declined")


    def test_process_raises_on_zero_amount(self):
        with self.assertRaises(ValueError):
            self.proc.process(self._make_tx(amount=0.0))

        self.gateway.charge.assert_not_called()
        self.audit.record.assert_not_called()


    def test_process_raises_on_negative_amount(self):
        with self.assertRaises(ValueError):
            self.proc.process(self._make_tx(amount=-10.0))

        self.gateway.charge.assert_not_called()
        self.audit.record.assert_not_called()

    def test_process_raises_when_amount_exceeds_limit(self):
        with self.assertRaises(ValueError):
            self.proc.process(self._make_tx(amount=10001.0))

        self.gateway.charge.assert_not_called()
        self.audit.record.assert_not_called()


    def test_process_accepts_amount_at_max_limit(self):
        self.gateway.charge.return_value = True
        self.assertEqual(self.proc.process(self._make_tx(amount=10000)), "success")


    def test_audit_records_charged_event_on_success(self):
        self.gateway.charge.return_value = True
        tx = self._make_tx()
        self.proc.process(tx)

        self.audit.record.assert_called_once_with(
            "CHARGED", tx.tx_id, {"amount": tx.amount}
        )

    def test_audit_records_declined_event_on_failure(self):
        self.gateway.charge.return_value = False
        tx = self._make_tx()
        self.proc.process(tx)

        self.audit.record.assert_called_once_with(
            "DECLINED", tx.tx_id, {"amount": tx.amount}
        )

    def test_audit_not_called_when_validation_fails(self):
        with self.assertRaises(ValueError):
            self.proc.process(self._make_tx(amount=-10.0))

        self.audit.record.assert_not_called()


# Task 2


class TestFraudAwareProcessor(unittest.TestCase):

    def setUp(self):
        self.gateway = MagicMock()
        self.detector = MagicMock()
        self.mailer = MagicMock()
        self.audit = MagicMock()
        self.proc = FraudAwareProcessor(self.gateway, self.detector, self.mailer, self.audit)
    
    def _create_result(self, risk_score = 0.1):
        approved = risk_score >= 0.75
        return FraudCheckResult(approved, risk_score, "Suspicious" if not approved else "")
    
    def _make_tx(self, amount=100.00, tx_id="TX-001", user_id=1):
        """Helper: build a Transaction. Keeps test setup DRY.
        Default values mean each test only specifies what it cares about."""

        return Transaction(tx_id=tx_id, user_id=user_id, amount=amount)


    def test_high_risk_returns_blocked(self):
        self.detector.check.return_value = self._create_result(0.9)
        result = self.proc.process(self._make_tx())
        self.assertEqual(result, "blocked")


    def test_high_risk_does_not_charge_the_card(self):
        self.detector.check.return_value = self._create_result(0.9)
        self.proc.process(self._make_tx())

        self.gateway.charge.assert_not_called()


    def test_exactly_at_threshold_is_treated_as_fraud(self):
        self.detector.check.return_value = self._create_result(0.75)
        result = self.proc.process(self._make_tx())
        self.assertEqual(result, "blocked")


    def test_just_below_threshold_is_not_blocked(self):
        self.detector.check.return_value = self._create_result(0.1)
        result = self.proc.process(self._make_tx())
        self.assertEqual(result, "success")


    def test_fraud_alert_email_sent_with_correct_args(self):
        self.detector.check.return_value = self._create_result(0.9)
        tx_id = "TX-FRAUD"
        user_id = 11
        self.proc.process(self._make_tx(tx_id=tx_id, user_id=user_id))
        self.mailer.send_fraud_alert.assert_called_once_with(user_id, tx_id)


    def test_fraud_audit_records_blocked_event(self):
        self.detector.check.return_value = self._create_result(0.9)
        tx_id = "TX-FRAUD"
        self.proc.process(self._make_tx(tx_id=tx_id))

        self.audit.record.assert_called_once_with(
            "BLOCKED", tx_id, { "risk": 0.9 }
        )


    def test_low_risk_successful_charge_returns_success(self):
        self.detector.check.return_value = self._create_result(0.1)
        self.gateway.charge.return_value = True
        result = self.proc.process(self._make_tx())
        self.assertEqual(result, "success")


    def test_receipt_email_sent_on_successful_charge(self):
        self.detector.check.return_value = self._create_result(0.1)
        self.gateway.charge.return_value = True
        tx_id = "TX-NOT-FRAUD"
        user_id = 11
        amount = 200
        self.proc.process(self._make_tx(tx_id=tx_id, user_id=user_id, amount=amount))

        self.mailer.send_receipt.assert_called_once_with(user_id, tx_id, amount)


    def test_fraud_alert_not_sent_on_successful_charge(self):
        self.detector.check.return_value = self._create_result(0.1)
        self.gateway.charge.return_value = True
        self.proc.process(self._make_tx())
        
        self.mailer.send_fraud_alert.assert_not_called()


    def test_low_risk_declined_charge_returns_declined(self):
        self.detector.check.return_value = self._create_result(0.1)
        self.gateway.charge.return_value = False
        result = self.proc.process(self._make_tx())

        self.assertEqual(result, "declined")


    def test_receipt_not_sent_on_declined_charge(self):
        self.detector.check.return_value = self._create_result(0.1)
        self.gateway.charge.return_value = False
        self.proc.process(self._make_tx())

        self.mailer.send_receipt.assert_not_called()


    def test_fraud_detector_connection_error_propagates(self):
        self.detector.check.side_effect = ConnectionError("Fraud detector cannot connect")

        with self.assertRaises(ConnectionError):
            self.proc.process(self._make_tx())
        
        self.gateway.charge.assert_not_called()
        self.mailer.send_receipt.assert_not_called()


# Task 3

class TestStatementBuilder(unittest.TestCase):

    def setUp(self):
        self.repo = MagicMock()
        self.builder = StatementBuilder(self.repo)
        

    def _make_tx(self, amount=100.00, tx_id="TX-001", user_id=1, status="pending"):
        """Helper: build a Transaction. Keeps test setup DRY.
        Default values mean each test only specifies what it cares about."""

        return Transaction(tx_id=tx_id, user_id=user_id, amount=amount, status=status)

    
    def test_empty_transaction_list_returns_zero_totals(self):
        self.repo.find_by_user.return_value = []
        result = self.builder.build(user_id=1)

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["total_charged"], 0)
        self.assertIsInstance(result["transactions"], list)
        
        
    def test_only_success_transactions_are_counted_in_total(self):
        self.repo.find_by_user.return_value = [
            self._make_tx(123, "TX-001", 3, "success"),
            self._make_tx(124, "TX-002", 3, "success"),
            self._make_tx(532, "TX-003", 3, "declined"),
            self._make_tx(193, "TX-004", 3, "success"),
            self._make_tx(181, "TX-005", 3, "pending")
        ]

        result = self.builder.build(user_id=3)

        self.assertEqual(result["total_charged"], 123 + 124 + 193)
        self.assertEqual(result["count"], 5)


    def test_all_success_transactions_summed(self):
        self.repo.find_by_user.return_value = [
            self._make_tx(123, "TX-001", 3, "success"),
            self._make_tx(124, "TX-002", 3, "success"),
            self._make_tx(193, "TX-004", 3, "success"),
        ]

        result = self.builder.build(user_id=3)

        self.assertEqual(result["total_charged"], 123 + 124 + 193)


    def test_total_is_rounded_to_two_decimal_places(self):
        self.repo.find_by_user.return_value = [
            self._make_tx(0.1000001, "TX-001", 3, "success"),
            self._make_tx(0.2000001, "TX-002", 3, "success"),
        ]

        result = self.builder.build(user_id=3)

        self.assertEqual(result["total_charged"], 0.3)


    def test_transactions_list_is_returned_unchanged(self):
        tx_list = [
            self._make_tx(0.1000001, "TX-001", 3, "success"),
            self._make_tx(0.2000001, "TX-002", 3, "success"),
        ]
        self.repo.find_by_user.return_value = tx_list

        result = self.builder.build(user_id=3)

        self.assertEqual(result["transactions"], tx_list)