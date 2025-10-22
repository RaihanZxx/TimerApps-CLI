#!/usr/bin/env python3
"""
Daemon process management for TimerApps background monitoring.
Handles proper daemonization, PID tracking, and lifecycle management.
"""

import os
import sys
import signal
import time
import atexit
import subprocess
from pathlib import Path
from typing import Optional

from .utils import log_message


class DaemonManager:
    """Manage background daemon process for app monitoring."""
    
    def __init__(self):
        self.pid_file = Path.home() / ".timerapps" / "daemon.pid"
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.daemon_log = Path.home() / ".timerapps" / "daemon.log"
    
    def get_daemon_pid(self) -> Optional[int]:
        """Get stored daemon PID."""
        try:
            if self.pid_file.exists():
                pid = int(self.pid_file.read_text().strip())
                # Check if process actually exists
                if self._process_exists(pid):
                    return pid
                else:
                    # Stale PID file
                    self.pid_file.unlink()
            return None
        except (ValueError, IOError):
            return None
    
    def _process_exists(self, pid: int) -> bool:
        """Check if process with given PID exists."""
        try:
            os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
            return True
        except (OSError, ProcessLookupError):
            return False
    
    def _write_pid(self, pid: int) -> None:
        """Write daemon PID to file."""
        try:
            self.pid_file.write_text(f"{pid}\n")
            os.chmod(self.pid_file, 0o644)
        except IOError as e:
            log_message(f"Failed to write PID file: {e}", "ERROR")
    
    def _daemonize(self) -> None:
        """Daemonize the process (double fork technique)."""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                # Exit parent process
                sys.exit(0)
            
            # Decouple from parent environment
            os.chdir("/")
            os.setsid()
            os.umask(0o022)
            
            # Second fork to prevent reacquiring terminal
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
            
            # Redirect file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            
            stdin = open("/dev/null", "r")
            stdout = open(str(self.daemon_log), "a+")
            stderr = open(str(self.daemon_log), "a+")
            
            os.dup2(stdin.fileno(), sys.stdin.fileno())
            os.dup2(stdout.fileno(), sys.stdout.fileno())
            os.dup2(stderr.fileno(), sys.stderr.fileno())
            
            # Write PID
            self._write_pid(os.getpid())
            
            # Register cleanup
            atexit.register(self._cleanup)
            
            log_message(f"Daemon started with PID {os.getpid()}")
        
        except OSError as e:
            log_message(f"Failed to daemonize: {e}", "ERROR")
            sys.exit(1)
    
    def _cleanup(self) -> None:
        """Cleanup on exit."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            log_message("Daemon stopped")
        except Exception as e:
            log_message(f"Cleanup error: {e}", "ERROR")
    
    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown on signals."""
        def signal_handler(signum, frame):
            log_message(f"Received signal {signum}, shutting down gracefully...")
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def start_daemon(self) -> bool:
        """Start monitoring as daemon."""
        # Check if already running
        existing_pid = self.get_daemon_pid()
        if existing_pid:
            log_message(f"Daemon already running with PID {existing_pid}")
            return False
        
        # Daemonize
        self._daemonize()
        self._setup_signal_handlers()
        
        return True
    
    def stop_daemon(self) -> bool:
        """Stop the running daemon."""
        pid = self.get_daemon_pid()
        if not pid:
            log_message("Daemon is not running")
            return False
        
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to exit
            for _ in range(50):  # 5 seconds timeout
                if not self._process_exists(pid):
                    log_message(f"Daemon (PID {pid}) stopped")
                    return True
                time.sleep(0.1)
            
            # Force kill if necessary
            os.kill(pid, signal.SIGKILL)
            log_message(f"Daemon (PID {pid}) forcefully killed")
            return True
        
        except (OSError, ProcessLookupError) as e:
            log_message(f"Error stopping daemon: {e}", "ERROR")
            return False
    
    def get_status(self) -> dict:
        """Get daemon status."""
        pid = self.get_daemon_pid()
        
        return {
            "running": pid is not None,
            "pid": pid,
            "log_file": str(self.daemon_log),
            "pid_file": str(self.pid_file)
        }
    
    def restart_daemon(self) -> bool:
        """Restart daemon."""
        self.stop_daemon()
        time.sleep(0.5)
        return self.start_daemon()
    
    def run_monitoring(self) -> None:
        """Run monitoring loop (called after daemonization)."""
        from .config_manager import ConfigManager
        from .adb_handler import ADBHandler
        from .app_monitor import AppMonitor
        from .notifications import NotificationManager
        
        config_mgr = ConfigManager()
        adb = ADBHandler(use_root=config_mgr.get_device_rooted() or False)
        notify_enabled = config_mgr.config["settings"]["notifications_enabled"]
        notify = NotificationManager(enabled=notify_enabled)
        monitor = AppMonitor(config_mgr, adb, notify)
        
        try:
            # Send daemon started notification
            apps_count = len(config_mgr.get_all_apps())
            notify.send_monitoring_started(apps_count)
            
            monitor.start()
            
            # Keep running
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            log_message("Daemon interrupted")
            # Send daemon stopped notification
            notify.send_monitoring_stopped()
            if monitor.is_running():
                monitor.stop()
        except Exception as e:
            log_message(f"Daemon error: {e}", "ERROR")
            if monitor and monitor.is_running():
                monitor.stop()
