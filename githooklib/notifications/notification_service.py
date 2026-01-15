from typing import List, Optional

from .providers import (
    BaseNotifier,
    SlackNotifier,
    WebhookNotifier,
    DesktopNotifier,
    EmailNotifier,
)
from ..config.config_schema import NotificationsConfig
from ..logger import get_logger

logger = get_logger()


class NotificationService:
    def __init__(self, config: NotificationsConfig) -> None:
        self.config = config
        self.notifiers: List[BaseNotifier] = []
        self._initialize_notifiers()
    
    def _initialize_notifiers(self) -> None:
        logger.trace("Initializing notification providers")
        
        if not self.config.enabled:
            logger.trace("Notifications disabled in config")
            return
        
        if self.config.slack.enabled and self.config.slack.webhook_url:
            logger.trace("Initializing Slack notifier")
            self.notifiers.append(
                SlackNotifier(
                    webhook_url=self.config.slack.webhook_url,
                    enabled=True,
                )
            )
        
        if self.config.webhook.enabled and self.config.webhook.webhook_url:
            logger.trace("Initializing Webhook notifier")
            self.notifiers.append(
                WebhookNotifier(
                    webhook_url=self.config.webhook.webhook_url,
                    enabled=True,
                )
            )
        
        if self.config.desktop.enabled:
            logger.trace("Initializing Desktop notifier")
            self.notifiers.append(
                DesktopNotifier(enabled=True)
            )
        
        if (
            self.config.email.enabled
            and self.config.email.smtp_server
            and self.config.email.email_to
        ):
            logger.trace("Initializing Email notifier")
            self.notifiers.append(
                EmailNotifier(
                    smtp_server=self.config.email.smtp_server,
                    smtp_port=self.config.email.smtp_port,
                    smtp_username=self.config.email.smtp_username or "",
                    smtp_password=self.config.email.smtp_password or "",
                    email_to=self.config.email.email_to,
                    enabled=True,
                )
            )
        
        logger.debug("Initialized %d notification provider(s)", len(self.notifiers))
    
    def should_notify(self, success: bool) -> bool:
        if not self.config.enabled:
            return False
        
        if success and not self.config.on_success:
            return False
        
        if not success and not self.config.on_failure:
            return False
        
        return True
    
    def notify(
        self,
        hook_name: str,
        success: bool,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        if not self.should_notify(success):
            logger.trace("Notification skipped (conditions not met)")
            return
        
        if not self.notifiers:
            logger.trace("No notifiers configured")
            return
        
        logger.debug(
            "Sending notifications for hook '%s' (success=%s) via %d provider(s)",
            hook_name,
            success,
            len(self.notifiers),
        )
        
        for notifier in self.notifiers:
            if not notifier.is_enabled():
                logger.trace("Skipping disabled notifier: %s", type(notifier).__name__)
                continue
            
            try:
                logger.trace("Sending via %s", type(notifier).__name__)
                result = notifier.send(hook_name, success, message, details)
                if result:
                    logger.trace("%s notification sent successfully", type(notifier).__name__)
                else:
                    logger.trace("%s notification failed", type(notifier).__name__)
            except Exception as e:
                logger.error(
                    "Error sending notification via %s: %s",
                    type(notifier).__name__,
                    e,
                )
                logger.trace("Exception details: %s", e, exc_info=True)


__all__ = ["NotificationService"]

