from datetime import datetime

class AuditService:
    def __init__(self, logger, clock=None):
        self._logger = logger
        self._clock  = clock or datetime.utcnow

    def record_action(self, user_id: int, action: str) -> None:
        if not action.strip():
            raise ValueError("Action cannot be blank")
        timestamp = self._clock().isoformat()
        self._logger.log(
            level="INFO",
            message=f"[{timestamp}] user={user_id} action={action}"
        )

    def record_error(self, user_id: int, error: str) -> None:
        timestamp = self._clock().isoformat()
        self._logger.log(
            level="ERROR",
            message=f"[{timestamp}] user={user_id} error={error}"
        )
        self._logger.alert(f"Error for user {user_id}")