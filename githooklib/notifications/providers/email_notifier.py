from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .base_notifier import BaseNotifier
from ...logger import get_logger

logger = get_logger()


class EmailNotifier(BaseNotifier):
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        email_to: List[str],
        enabled: bool = True,
    ) -> None:
        super().__init__(enabled)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.email_to = email_to
    
    def send(
        self,
        hook_name: str,
        success: bool,
        message: Optional[str] = None,
        details: Optional[str] = None,
    ) -> bool:
        if not self.enabled:
            logger.trace("Email notifier is disabled")
            return False
        
        if not self.email_to:
            logger.warning("No email recipients configured")
            return False
        
        logger.debug("Sending email notification for hook: %s", hook_name)
        
        status = "Success" if success else "Failed"
        subject = f"Git Hook {hook_name}: {status}"
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_username
        msg["To"] = ", ".join(self.email_to)
        
        text_content = f"""
Git Hook Notification
=====================

Hook: {hook_name}
Status: {status}
"""
        
        if message:
            text_content += f"\nMessage: {message}"
        
        if details:
            text_content += f"\n\nDetails:\n{details}"
        
        html_content = f"""
<html>
<head></head>
<body>
    <h2>Git Hook Notification</h2>
    <table border="0" cellpadding="5" cellspacing="0">
        <tr>
            <td><strong>Hook:</strong></td>
            <td>{hook_name}</td>
        </tr>
        <tr>
            <td><strong>Status:</strong></td>
            <td style="color: {'green' if success else 'red'};">{status}</td>
        </tr>
"""
        
        if message:
            html_content += f"""
        <tr>
            <td><strong>Message:</strong></td>
            <td>{message}</td>
        </tr>
"""
        
        html_content += """
    </table>
"""
        
        if details:
            html_content += f"""
    <h3>Details</h3>
    <pre>{details}</pre>
"""
        
        html_content += """
</body>
</html>
"""
        
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(
                    self.smtp_username,
                    self.email_to,
                    msg.as_string(),
                )
            
            logger.debug("Email notification sent successfully")
            return True
        except Exception as e:
            logger.error("Error sending email notification: %s", e)
            logger.trace("Exception details: %s", e, exc_info=True)
            return False


__all__ = ["EmailNotifier"]

