from typing import Optional
import json

from .base_notifier import BaseNotifier
from ...logger import get_logger
from ...command import CommandExecutor

logger = get_logger()


class SlackNotifier(BaseNotifier):
    def __init__(self, webhook_url: str, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.webhook_url = webhook_url
        self.executor = CommandExecutor()
    
    def send(
        self,
        hook_name: str,
        success: bool,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.trace("Slack notifier is disabled")
            return False
        
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        logger.debug("Sending Slack notification for hook: %s", hook_name)
        
        color = "good" if success else "danger"
        status_emoji = ":white_check_mark:" if success else ":x:"
        status_text = "Success" if success else "Failed"
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} Git Hook: {hook_name}",
                    "fields": [
                        {
                            "title": "Status",
                            "value": status_text,
                            "short": True,
                        },
                    ],
                }
            ]
        }
        
        if message:
            payload["attachments"][0]["fields"].append({
                "title": "Message",
                "value": message,
                "short": False,
            })
        
        if details:
            payload["attachments"][0]["fields"].append({
                "title": "Details",
                "value": f"```{details}```",
                "short": False,
            })
        
        try:
            import requests
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=5,
            )
            
            if response.status_code == 200:
                logger.debug("Slack notification sent successfully")
                return True
            else:
                logger.warning(
                    "Failed to send Slack notification: %d %s",
                    response.status_code,
                    response.text,
                )
                return False
        except ImportError:
            logger.warning("requests library not installed, trying curl")
            return self._send_via_curl(payload)
        except Exception as e:
            logger.error("Error sending Slack notification: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
            return False
    
    def _send_via_curl(self, payload: dict) -> bool:
        logger.trace("Attempting to send via curl")
        try:
            json_data = json.dumps(payload)
            result = self.executor.run([
                "curl",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json_data,
                self.webhook_url,
            ])
            
            if result.success:
                logger.debug("Slack notification sent via curl")
                return True
            else:
                logger.warning("Failed to send via curl: %s", result.stderr)
                return False
        except Exception as e:
            logger.error("Error sending via curl: %s", e)
            return False


__all__ = ["SlackNotifier"]

