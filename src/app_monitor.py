import threading
import time
from datetime import datetime
from typing import Callable, Optional, Dict, Set
from enum import Enum

from .adb_handler import ADBHandler
from .config_manager import ConfigManager
from .notifications import NotificationManager
from .utils import log_message, get_today_date, seconds_to_minutes


class TimerState(Enum):
    INACTIVE = "inactive"      # App not running
    MONITORING = "monitoring"  # Timer actively counting
    PAUSED = "paused"          # App stopped, timer paused
    BLOCKED = "blocked"        # Limit reached, app killed/frozen


class AppMonitor:
    """Monitor app usage with smart pause/resume logic."""
    
    def __init__(self, config_manager: ConfigManager, adb_handler: ADBHandler,
                 notify_manager: Optional[NotificationManager] = None):
        self.config = config_manager
        self.adb = adb_handler
        self.notify = notify_manager
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # App tracking state
        self._last_active_app: Optional[str] = None
        self._app_states: Dict[str, TimerState] = {}
        self._app_session_start: Dict[str, float] = {}
        self._app_total_seconds: Dict[str, int] = {}  # Total seconds used today
        self._app_5min_warning_sent: Set[str] = set()  # Track which apps sent 5min warning
        
        self._check_interval = config_manager.config["settings"]["check_interval"]
    
    def _initialize_app_state(self, package: str) -> None:
        """Initialize tracking state for an app."""
        if package not in self._app_states:
            self._app_states[package] = TimerState.INACTIVE
            self._app_session_start[package] = None
            
            # Load from database if available
            used = self.config.get_total_usage(package)
            self._app_total_seconds[package] = used * 60
    
    def _update_total_usage(self) -> None:
        """Update all app usage in database."""
        today = get_today_date()
        for package, total_seconds in self._app_total_seconds.items():
            minutes = seconds_to_minutes(total_seconds)
            self.config.update_app_usage(package, minutes)
    
    def start(self) -> None:
        """Start monitoring."""
        if self._running:
            return
        
        with self._lock:
            self._running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            log_message("Monitor started")
    
    def stop(self) -> None:
        """Stop monitoring."""
        if not self._running:
            return
        
        with self._lock:
            self._running = False
            self._update_total_usage()
        
        if self._thread:
            self._thread.join(timeout=5)
        
        log_message("Monitor stopped")
    
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        try:
            while self._running:
                # Check and reset daily if needed
                if self.config.check_and_reset_daily():
                    # Unfreeze all apps on daily reset
                    for package in self.config.get_all_apps().keys():
                        if self.config.get_app(package)["action"] == "freeze":
                            self.adb.unfreeze_app(package)
                    
                    self._app_total_seconds.clear()
                    self._app_session_start.clear()
                    self._app_states.clear()
                    self._app_5min_warning_sent.clear()
                    log_message("Daily reset performed - all apps unfrozen")
                
                # Get currently active app
                current_active = self.adb.get_active_app()
                
                # Initialize monitored apps
                for package in self.config.get_all_apps().keys():
                    self._initialize_app_state(package)
                
                # Update states for all monitored apps
                for package in self.config.get_all_apps().keys():
                    self._update_app_state(package, current_active)
                
                self._update_total_usage()
                time.sleep(self._check_interval)
        
        except Exception as e:
            log_message(f"Monitor loop error: {e}", "ERROR")
    
    def _update_app_state(self, package: str, current_active: Optional[str]) -> None:
        """Update state for a single app."""
        app_config = self.config.get_app(package)
        if not app_config or not app_config["enabled"]:
            return
        
        current_state = self._app_states.get(package, TimerState.INACTIVE)
        is_active = current_active == package
        used_seconds = self._app_total_seconds.get(package, 0)
        limit_seconds = app_config["limit_minutes"] * 60
        
        # STATE MACHINE
        if is_active:
            if current_state == TimerState.BLOCKED:
                # Stay blocked
                pass
            elif current_state == TimerState.PAUSED:
                # Resume timer
                self._app_states[package] = TimerState.MONITORING
                self._app_session_start[package] = time.time()
                log_message(f"Resume monitoring: {package}")
            elif current_state == TimerState.MONITORING:
                # Continue monitoring, update time
                if self._app_session_start[package]:
                    elapsed = time.time() - self._app_session_start[package]
                    self._app_total_seconds[package] += int(elapsed)
                    self._app_session_start[package] = time.time()
            else:  # INACTIVE
                # Start monitoring
                self._app_states[package] = TimerState.MONITORING
                self._app_session_start[package] = time.time()
                log_message(f"Start monitoring: {package}")
            
            # Check if 5 minutes remaining (send warning once)
            remaining_seconds = limit_seconds - self._app_total_seconds[package]
            remaining_minutes = seconds_to_minutes(remaining_seconds)
            
            if remaining_minutes <= 5 and remaining_minutes > 0 and package not in self._app_5min_warning_sent:
                # Send 5-minute warning notification
                app_name = app_config["name"]
                used_minutes = seconds_to_minutes(self._app_total_seconds[package])
                content = f"Used: {used_minutes}m / {app_config['limit_minutes']}m - Remaining: {remaining_minutes}m"
                self.notify.send_custom(
                    f"{app_name} - 5 Minutes Left",
                    content,
                    icon="@android:drawable/ic_dialog_alert"
                )
                self._app_5min_warning_sent.add(package)
                log_message(f"5-minute warning sent for {app_name}")
            
            # Check if limit reached
            if self._app_total_seconds[package] >= limit_seconds:
                self._enforce_limit(package, app_config)
        else:
            # App not active
            if current_state == TimerState.MONITORING:
                # Pause timer
                if self._app_session_start[package]:
                    elapsed = time.time() - self._app_session_start[package]
                    self._app_total_seconds[package] += int(elapsed)
                    self._app_session_start[package] = None
                
                self._app_states[package] = TimerState.PAUSED
                log_message(f"Pause monitoring: {package} (used: {seconds_to_minutes(self._app_total_seconds[package])}m)")
    
    def _enforce_limit(self, package: str, app_config: Dict) -> None:
        """Enforce app limit by killing or freezing."""
        current_state = self._app_states.get(package)
        if current_state == TimerState.BLOCKED:
            return  # Already blocked
        
        action = app_config["action"]
        app_name = app_config["name"]
        
        # Mark limit reached
        self.config.mark_limit_reached(package)
        
        # Send notification
        if self.notify:
            self.notify.send_limit_reached(app_name, app_config["limit_minutes"])
        
        log_message(f"Limit reached for {app_name}, action: {action}")
        
        # Execute action
        if action == "freeze":
            success = self.adb.freeze_app(package)
        else:  # kill
            success = self.adb.kill_app(package)
        
        if success:
            self._app_states[package] = TimerState.BLOCKED
    
    def get_app_state(self, package: str) -> TimerState:
        """Get current state of an app."""
        self._initialize_app_state(package)
        return self._app_states.get(package, TimerState.INACTIVE)
    
    def get_app_used_time(self, package: str) -> int:
        """Get total used time in seconds for app."""
        return self._app_total_seconds.get(package, 0)
    
    def get_app_used_minutes(self, package: str) -> int:
        """Get total used time in minutes for app."""
        return seconds_to_minutes(self.get_app_used_time(package))
    
    def get_all_app_times(self) -> Dict[str, int]:
        """Get all app times in minutes."""
        result = {}
        for package, seconds in self._app_total_seconds.items():
            result[package] = seconds_to_minutes(seconds)
        return result
    
    def reset_app(self, package: str) -> bool:
        """Reset an app's timer manually."""
        with self._lock:
            if package in self._app_total_seconds:
                self._app_total_seconds[package] = 0
                self._app_session_start[package] = None
                self._app_states[package] = TimerState.INACTIVE
                self.config.reset_app_timer(package)
                log_message(f"Reset timer for {package}")
                return True
        return False
    
    def reset_all(self) -> int:
        """Reset all timers. Returns count of reset apps."""
        with self._lock:
            count = 0
            for package in list(self._app_total_seconds.keys()):
                if self.reset_app(package):
                    count += 1
            return count
