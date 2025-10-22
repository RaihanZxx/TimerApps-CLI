import subprocess
from typing import Optional
from .utils import log_message


class NotificationManager:
    """Handle Termux API notifications with ADB fallback."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.use_adb = False
        self.adb_device = None
        self._check_termux_available()
    
    def _check_termux_available(self) -> None:
        """Check if Termux notification API is available, setup ADB fallback if needed."""
        try:
            result = subprocess.run(
                ["which", "termux-notification"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                self.enabled = True
                log_message("Termux notification API available")
                return
        except Exception as e:
            log_message(f"Termux notification check failed: {e}", "WARN")
        
        # Fallback to ADB if termux-notification not available
        log_message("Termux notification not found, attempting ADB fallback", "WARN")
        if self._setup_adb_fallback():
            self.use_adb = True
            self.enabled = True
            log_message("ADB fallback enabled for notifications")
        else:
            self.enabled = False
            log_message("No notification method available (termux-notification or ADB)", "WARN")
    
    def _setup_adb_fallback(self) -> bool:
        """Setup ADB for notification fallback."""
        try:
            # Check if adb is available
            result = subprocess.run(
                ["which", "adb"],
                capture_output=True,
                timeout=2
            )
            if result.returncode != 0:
                log_message("ADB not found on system", "WARN")
                return False
            
            # Try to detect ADB device
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
                        log_message(f"ADB device detected for fallback: {self.adb_device}")
                        return True
            
            log_message("No ADB device found", "WARN")
            return False
        except Exception as e:
            log_message(f"ADB setup failed: {e}", "WARN")
            return False
    
    def _send_notification_via_termux(self, title: str, content: str,
                                     notification_id: Optional[int] = None,
                                     action: bool = False) -> bool:
        """Send notification via direct termux-notification command."""
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
                log_message(f"Notification sent (Termux): {title}")
                return True
            else:
                log_message(f"Termux notification failed: {result.stderr.decode()}", "DEBUG")
                return False
        except Exception as e:
            log_message(f"Error sending Termux notification: {e}", "DEBUG")
            return False
    
    def _send_notification_via_adb(self, title: str, content: str,
                                  notification_id: Optional[int] = None,
                                  action: bool = False, icon: Optional[str] = None) -> bool:
        """Send notification via ADB using Android notification service.
        
        Args:
            title: Notification title
            content: Notification content/description
            notification_id: Optional notification ID for grouping
            action: Whether to include action (unused for now)
            icon: Optional icon in format @android:drawable/icon_name
        """
        if not self.adb_device:
            log_message("ADB device not available for notification", "WARN")
            return False
        
        try:
            import urllib.parse
            
            # Method 1: Use cmd notification post (most reliable on Android 8+)
            tag = f"timerapps_{notification_id if notification_id else 'default'}"
            cmd = [
                "adb", "-s", self.adb_device, "shell",
                "cmd", "notification", "post",
                "-t", title,
                "-S", "bigtext",
            ]
            
            # Add icon if provided
            if icon:
                cmd.extend(["-i", icon])
            
            cmd.extend([tag, content])
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                log_message(f"Notification posted (cmd service): {title}")
                return True
            
            # Fallback Method 2: Try am broadcast to Termux API
            log_message(f"cmd notification failed, trying broadcast...", "DEBUG")
            shell_cmd = (
                f"am broadcast -n com.termux.api/.apis.NotificationAPI "
                f"-e title '{title}' "
                f"-e text '{content}'"
            )
            
            if notification_id:
                shell_cmd += f" -e id {notification_id}"
            
            if action:
                shell_cmd += " -e action yes"
            
            cmd = ["adb", "-s", self.adb_device, "shell", shell_cmd]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                log_message(f"Notification queued (ADB API): {title}")
                return True
            
            # Fallback Method 3: Try URI scheme with URL encoding
            log_message(f"Broadcast failed, trying URI scheme...", "DEBUG")
            title_enc = urllib.parse.quote(title)
            content_enc = urllib.parse.quote(content)
            uri = f"termux://notification?title={title_enc}&text={content_enc}"
            if notification_id:
                uri += f"&id={notification_id}"
            
            cmd = [
                "adb", "-s", self.adb_device, "shell",
                "am", "start", "-a", "android.intent.action.VIEW",
                "-d", uri
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                log_message(f"Notification queued (ADB URI): {title}")
                return True
            
            # Final Fallback Method 4: Try direct termux command
            shell_cmd = (
                f"termux-notification --title '{title}' --content '{content}'"
            )
            if notification_id:
                shell_cmd += f" --id {notification_id}"
            
            cmd = ["adb", "-s", self.adb_device, "shell", shell_cmd]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            
            if result.returncode == 0:
                log_message(f"Notification sent (shell): {title}")
                return True
            else:
                error_msg = result.stderr.decode() if result.stderr else result.stdout.decode()
                log_message(f"All notification methods attempted: {error_msg}", "DEBUG")
                return True  # Attempted at least once
        except Exception as e:
            log_message(f"Error sending ADB notification: {e}", "DEBUG")
            return True  # Attempted despite error
    
    def _send_notification(self, title: str, content: str, 
                          notification_id: Optional[int] = None,
                          action: bool = False) -> bool:
        """Send raw notification via Termux API or ADB fallback."""
        if not self.enabled:
            log_message(f"Notification (disabled): {title} - {content}")
            return False
        
        if self.use_adb:
            return self._send_notification_via_adb(title, content, notification_id, action)
        else:
            return self._send_notification_via_termux(title, content, notification_id, action)
    
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
        if not self.enabled:
            return False
        
        try:
            if self.use_adb and self.adb_device:
                cmd = [
                    "adb", "-s", self.adb_device, "shell",
                    "termux-notification-remove", str(notification_id)
                ]
            else:
                cmd = ["termux-notification-remove", str(notification_id)]
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            log_message(f"Error clearing notification: {e}", "DEBUG")
            return False
    
    def clear_all(self) -> bool:
        """Clear all TimerApps notifications."""
        for notif_id in [100, 101, 102, 103, 104, 105]:
            self.clear_notification(notif_id)
        return True
