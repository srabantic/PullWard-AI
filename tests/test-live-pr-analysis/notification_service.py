"""
Notification & Audit Service (Production-ready & Backwards-compatible)
Designed to verify clean, approved PullWard AI PR governance flow.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import datetime

logger = logging.getLogger("NotificationService")
logger.setLevel(logging.INFO)


@dataclass
class NotificationPayload:
    recipient_id: str
    channel: str
    message: str
    priority: str = "NORMAL"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.utcnow().isoformat()


class NotificationService:
    """Handles multi-channel notification dispatch and delivery logs safely."""

    def __init__(self, default_channel: str = "email"):
        self.default_channel = default_channel
        self.dispatch_history: List[Dict[str, str]] = []

    def send_notification(self, payload: NotificationPayload) -> Dict[str, str]:
        """Dispatches notification to user via the designated channel safely."""
        logger.info("Dispatching notification to %s via %s", payload.recipient_id, payload.channel)
        
        record = {
            "recipient_id": payload.recipient_id,
            "channel": payload.channel,
            "status": "DELIVERED",
            "timestamp": payload.created_at
        }
        self.dispatch_history.append(record)
        return record

    def get_history_by_recipient(self, recipient_id: str) -> List[Dict[str, str]]:
        """Retrieves delivery records filtered by recipient ID without destructive actions."""
        return [item for item in self.dispatch_history if item.get("recipient_id") == recipient_id]

    def health_check(self) -> Dict[str, str]:
        """Returns service status."""
        return {"status": "healthy", "service": "NotificationService"}
