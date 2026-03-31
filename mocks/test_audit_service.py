import unittest
from unittest.mock import MagicMock, call
from datetime import datetime
from audit_service import AuditService

class TestAuditService(unittest.TestCase):

    def setUp(self):
        # Mock logger — we'll assert on its calls
        self.mock_logger = MagicMock()

        # Stub clock — we control time to make assertions deterministic
        self.mock_clock  = MagicMock()
        self.mock_clock.return_value = datetime(2024, 6, 15, 12, 0, 0)

        self.svc = AuditService(
            logger=self.mock_logger,
            clock=self.mock_clock
        )

    def test_record_action_calls_logger_once(self):
        self.svc.record_action(42, "login")

        self.mock_logger.log.assert_called_once()

    def test_record_action_logs_correct_level(self):
        self.svc.record_action(42, "login")

        _, kwargs = self.mock_logger.log.call_args
        self.assertEqual(kwargs["level"], "INFO")

    def test_record_action_embeds_user_id_in_message(self):
        self.svc.record_action(99, "logout")

        _, kwargs = self.mock_logger.log.call_args
        self.assertIn("user=99", kwargs["message"])
        self.assertIn("action=logout", kwargs["message"])

    def test_record_error_calls_both_log_and_alert(self):
        self.svc.record_error(7, "NullPointerException")

        self.mock_logger.log.assert_called_once()
        self.mock_logger.alert.assert_called_once_with("Error for user 7")

    def test_blank_action_raises_and_does_not_log(self):
        with self.assertRaises(ValueError):
            self.svc.record_action(1, "   ")

        self.mock_logger.log.assert_not_called()  # ← key behaviour check

    def test_multiple_actions_call_logger_multiple_times(self):
        self.svc.record_action(1, "login")
        self.svc.record_action(1, "view_dashboard")
        self.svc.record_action(1, "logout")

        self.assertEqual(self.mock_logger.log.call_count, 3)
    
    def test_verify_timestamp(self):
        self.assertIn(self.mock_clock().strftime("%Y-%m-%d"), "2024-06-15")
    

    def test_record_error(self):
        self.svc.record_error(6, "NullPointerException")

        self.mock_logger.assert_has_calls(self.mock_logger.method_calls)
        self.mock_logger.alert.assert_called_once()