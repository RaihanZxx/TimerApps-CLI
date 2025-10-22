import subprocess
from typing import Optional
from .utils import log_message


class NotificationManager:
    """Handle Android notifications via ADB."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.adb_device = None
        self._setup_adb()
    
    def _setup_adb(self) -> None:
        """Setup ADB for notification delivery."""
        try:
            # Check if adb is available
            result = subprocess.run(
                ["which", "adb"],
                capture_output=True,
                timeout=2
            )
            if result.returncode != 0:
                log_message("ADB not found on system", "WARN")
                self.enabled = False
                return
            
            # Detect ADB device
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip() and "List of devices" not in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "device":
                        self.adb_device = parts[0]
                        log_message(f"ADB device detected: {self.adb_device}")
                        self.enabled = True
                        return
            
            log_message("No ADB device found", "WARN")
            self.enabled = False
        except Exception as e:
            log_message(f"ADB setup failed: {e}", "WARN")
            self.enabled = False
    

    def _send_notification_via_adb(self, title: str, content: str,
                                  notification_id: Optional[int] = None,
                                  icon: Optional[str] = None) -> bool:
        """Send notification via ADB using Android cmd notification service.
        
        Args:
            title: Notification title
            content: Notification content/description
            notification_id: Optional notification ID for grouping
            icon: Optional icon in format @android:drawable/icon_name
        """
        if not self.adb_device:
            log_message("ADB device not available for notification", "WARN")
            return False
        
        try:
            tag = f"timerapps_{notification_id if notification_id else 'default'}"
            cmd = [
                "adb", "-s", self.adb_device, "shell",
                "cmd", "notification", "post",
                "-t", title,
                "-S", "bigtext",
            ]
            
            if icon:
                cmd.extend(["-i", icon])
            
            cmd.extend([tag, content])
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                log_message(f"Notification posted: {title}")
                return True
            else:
                error_msg = result.stderr.decode() if result.stderr else result.stdout.decode()
                log_message(f"Notification failed: {error_msg}", "DEBUG")
                return False
        except Exception as e:
            log_message(f"Error sending notification: {e}", "DEBUG")
            return False
    
    def _send_notification(self, title: str, content: str, 
                          notification_id: Optional[int] = None) -> bool:
        """Send notification via Android notification service."""
        if not self.enabled:
            log_message(f"Notification (disabled): {title} - {content}")
            return False
        
        return self._send_notification_via_adb(title, content, notification_id)
    
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
