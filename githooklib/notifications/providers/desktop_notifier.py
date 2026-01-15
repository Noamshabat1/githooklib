from typing import Optional
import platform

from .base_notifier import BaseNotifier
from ...logger import get_logger
from ...command import CommandExecutor

logger = get_logger()


class DesktopNotifier(BaseNotifier):
    def __init__(self, enabled: bool = True) -> None:
        super().__init__(enabled)
        self.executor = CommandExecutor()
        self.system = platform.system()
    
    def send(
        self,
        hook_name: str,
        success: bool,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.trace("Desktop notifier is disabled")
            return False
        
        logger.debug("Sending desktop notification for hook: %s", hook_name)
        
        title = f"Git Hook: {hook_name}"
        status = "✓ Success" if success else "✗ Failed"
        body = f"{status}\n{message}" if message else status
        
        if self.system == "Windows":
            return self._send_windows(title, body)
        elif self.system == "Darwin":
            return self._send_macos(title, body)
        elif self.system == "Linux":
            return self._send_linux(title, body)
        else:
            logger.warning("Desktop notifications not supported on %s", self.system)
            return False
    
    def _send_windows(self, title: str, body: str) -> bool:
        logger.trace("Sending Windows notification")
        try:
            powershell_cmd = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$toastXml = [xml] $template.GetXml()
$toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) > $null
$toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{body}")) > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($toastXml.OuterXml)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Githooklib")
$notifier.Show($toast)
'''
            result = self.executor.run(
                ["powershell", "-Command", powershell_cmd],
                capture_output=True,
            )
            
            if result.success or result.exit_code == 0:
                logger.debug("Windows notification sent")
                return True
            else:
                logger.trace("PowerShell notification failed, trying fallback")
                return self._send_windows_fallback(title, body)
        except Exception as e:
            logger.trace("Error sending Windows notification: %s", e)
            return self._send_windows_fallback(title, body)
    
    def _send_windows_fallback(self, title: str, body: str) -> bool:
        logger.trace("Using Windows msg fallback")
        try:
            result = self.executor.run(
                ["msg", "*", f"{title}: {body}"],
                capture_output=True,
            )
            return result.success
        except Exception as e:
            logger.trace("Windows fallback failed: %s", e)
            return False
    
    def _send_macos(self, title: str, body: str) -> bool:
        logger.trace("Sending macOS notification")
        try:
            script = f'display notification "{body}" with title "{title}"'
            result = self.executor.run(
                ["osascript", "-e", script],
                capture_output=True,
            )
            
            if result.success:
                logger.debug("macOS notification sent")
                return True
            else:
                logger.warning("Failed to send macOS notification: %s", result.stderr)
                return False
        except Exception as e:
            logger.error("Error sending macOS notification: %s", e)
            return False
    
    def _send_linux(self, title: str, body: str) -> bool:
        logger.trace("Sending Linux notification")
        try:
            result = self.executor.run(
                ["notify-send", title, body],
                capture_output=True,
            )
            
            if result.success:
                logger.debug("Linux notification sent")
                return True
            else:
                logger.warning("Failed to send Linux notification: %s", result.stderr)
                logger.debug("Make sure 'notify-send' is installed (libnotify-bin)")
                return False
        except Exception as e:
            logger.error("Error sending Linux notification: %s", e)
            return False


__all__ = ["DesktopNotifier"]

