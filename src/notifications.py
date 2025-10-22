import subprocess
from typing import Optional
from .utils import log_message


class NotificationManager:
    """Handle Termux API notifications."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._check_termux_available()
    
    def _check_termux_available(self) -> None:
        """Check if Termux notification API is available."""
        try:
            subprocess.run(
                ["which", "termux-notification"],
                capture_output=True,
                timeout=2
            )
        except Exception as e:
            log_message(f"Termux notification not available: {e}", "WARN")
            self.enabled = False
    
    def _send_notification(self, title: str, content: str, 
                          notification_id: Optional[int] = None,
                          action: bool = False) -> bool:
        """Send raw notification via Termux API."""
        if not self.enabled:
            log_message(f"Notification (disabled): {title} - {content}")
            return False
        
        try:
            cmd = [
                "termux-notification",
                "--title", title,
                "--content", content,
            ]
            
            if notification_id:
                cmd.extend(["--id", str(notification_id)])
            
            if action:
                cmd.append("--action")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                log_message(f"Notification sent: {title}")
                return True
            else:
                log_message(f"Notification failed: {result.stderr.decode()}", "ERROR")
                return False
        except Exception as e:
            log_message(f"Error sending notification: {e}", "ERROR")
            return False
    
    def send_limit_reached(self, app_name: str, limit_minutes: int) -> bool:
        """Send notification when app limit is reached."""
        title = "TimerApps - Limit Reached"
        content = f"{app_name} limit ({limit_minutes}m) exceeded. App is now blocked."
        return self._send_notification(title, content, notification_id=100)
    
    def send_warning(self, app_name: str, remaining_minutes: int) -> bool:
        """Send warning notification when time is running out."""
        title = "TimerApps - Warning"
        content = f"{app_name}: Only {remaining_minutes}m remaining!"
        return self._send_notification(title, content, notification_id=101)
    
    def send_limit_reset(self, app_name: str) -> bool:
        """Send notification when daily limit is reset."""
        title = "TimerApps - Daily Reset"
        content = f"{app_name} limit has been reset for today."
        return self._send_notification(title, content, notification_id=102)
    
    def send_app_unfrozen(self, app_name: str) -> bool:
        """Send notification when app is unfrozen."""
        title = "TimerApps - App Unfrozen"
        content = f"{app_name} is now available again."
        return self._send_notification(title, content, notification_id=103)
    
    def send_monitoring_started(self, app_count: int) -> bool:
        """Send notification when monitoring starts."""
        title = "TimerApps - Monitoring Started"
        content = f"Monitoring {app_count} app(s)"
        return self._send_notification(title, content, notification_id=104)
    
    def send_monitoring_stopped(self) -> bool:
        """Send notification when monitoring stops."""
        title = "TimerApps - Monitoring Stopped"
        content = "All timers have been saved."
        return self._send_notification(title, content, notification_id=105)
    
    def send_custom(self, title: str, content: str, 
                   notification_id: Optional[int] = None) -> bool:
        """Send custom notification."""
        return self._send_notification(title, content, notification_id)
    
    def clear_notification(self, notification_id: int) -> bool:
        """Clear a notification by ID."""
        try:
            cmd = ["termux-notification-remove", str(notification_id)]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            log_message(f"Error clearing notification: {e}", "ERROR")
            return False
    
    def clear_all(self) -> bool:
        """Clear all TimerApps notifications."""
        for notif_id in [100, 101, 102, 103, 104, 105]:
            self.clear_notification(notif_id)
        return True
