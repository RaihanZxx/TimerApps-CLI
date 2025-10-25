import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
from .utils import (
    get_config_path, get_db_path, get_today_date, 
    dict_merge, log_message, ensure_timerapps_dir
)


DEFAULT_CONFIG = {
    "device": {
        "is_rooted": None,  # Will be auto-detected
        "use_adb": True,
    },
    "apps": {},
    "settings": {
        "check_interval": 5,
        "auto_reset_hour": 0,
        "notifications_enabled": True,
    },
    "last_reset_date": None,
}


class ConfigManager:
    def __init__(self):
        self.config_path = get_config_path()
        self.db_path = get_db_path()
        self.config = self._load_config()
        self.db = self._load_db()
    
    def _load_config(self) -> Dict:
        """Load config.json or create default."""
        ensure_timerapps_dir()
        
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    loaded = json.load(f)
                    return dict_merge(DEFAULT_CONFIG.copy(), loaded)
            except json.JSONDecodeError:
                log_message("Config corrupted, using defaults", "WARN")
                return DEFAULT_CONFIG.copy()
        
        # Create new config
        self.save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
    
    def _load_db(self) -> Dict:
        """Load db.json or create empty."""
        ensure_timerapps_dir()
        
        if self.db_path.exists():
            try:
                with open(self.db_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                log_message("Database corrupted, starting fresh", "WARN")
                return {}
        
        return {}
    
    def save_config(self, config: Optional[Dict] = None) -> None:
        """Save config to file."""
        ensure_timerapps_dir()
        data = config if config is not None else self.config
        
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)
        
        log_message(f"Config saved")
    
    def save_db(self, db: Optional[Dict] = None) -> None:
        """Save database to file."""
        ensure_timerapps_dir()
        data = db if db is not None else self.db
        
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2)
        
        log_message(f"Database saved")
    
    def reload(self) -> None:
        """Reload config and database from file."""
        self.config = self._load_config()
        self.db = self._load_db()
    
    # ========== CONFIG OPERATIONS ==========
    
    def set_device_rooted(self, is_rooted: bool) -> None:
        """Set device root status."""
        self.config["device"]["is_rooted"] = is_rooted
        self.config["device"]["use_adb"] = not is_rooted
        self.save_config()
    
    def get_device_rooted(self) -> Optional[bool]:
        """Get if device is rooted."""
        return self.config["device"]["is_rooted"]
    
    def add_app(self, package: str, name: str, limit_minutes: int, 
                action: str = "kill", enabled: bool = True) -> bool:
        """Add app to monitoring list."""
        if package in self.config["apps"]:
            return False  # Already exists
        
        self.config["apps"][package] = {
            "name": name,
            "limit_minutes": limit_minutes,
            "enabled": enabled,
            "action": action,  # "kill" or "freeze"
        }
        
        # Initialize in database
        today = get_today_date()
        if today not in self.db:
            self.db[today] = {}
        
        self.db[today][package] = {
            "name": name,
            "total_minutes_used": 0,
            "limit_minutes": limit_minutes,
            "remaining_minutes": limit_minutes,
            "sessions": [],
            "limit_reached": False,
            "blocked_at": None,
        }
        
        self.save_config()
        self.save_db()
        log_message(f"Added app: {name} ({package}) - {limit_minutes}m limit")
        return True
    
    def remove_app(self, package: str) -> bool:
        """Remove app from monitoring."""
        if package not in self.config["apps"]:
            return False
        
        del self.config["apps"][package]
        self.save_config()
        log_message(f"Removed app: {package}")
        return True
    
    def update_app_limit(self, package: str, limit_minutes: int) -> bool:
        """Update app time limit."""
        if package not in self.config["apps"]:
            return False
        
        self.config["apps"][package]["limit_minutes"] = limit_minutes
        self.save_config()
        log_message(f"Updated {package} limit to {limit_minutes}m")
        return True
    
    def update_app_name(self, package: str, name: str) -> bool:
        """Update app name."""
        if package not in self.config["apps"]:
            return False
        
        self.config["apps"][package]["name"] = name
        self.save_config()
        log_message(f"Updated {package} name to {name}")
        return True
    
    def update_app_action(self, package: str, action: str) -> bool:
        """Update app action (kill or freeze)."""
        if package not in self.config["apps"]:
            return False
        
        self.config["apps"][package]["action"] = action
        self.save_config()
        log_message(f"Updated {package} action to {action}")
        return True
    
    def get_app(self, package: str) -> Optional[Dict]:
        """Get app config by package name."""
        return self.config["apps"].get(package)
    
    def get_all_apps(self) -> Dict:
        """Get all monitored apps."""
        return self.config["apps"]
    
    def enable_app(self, package: str, enabled: bool = True) -> bool:
        """Enable/disable monitoring for an app."""
        if package not in self.config["apps"]:
            return False
        
        self.config["apps"][package]["enabled"] = enabled
        self.save_config()
        status = "enabled" if enabled else "disabled"
        log_message(f"App {package} {status}")
        return True
    
    # ========== DATABASE OPERATIONS ==========
    
    def get_today_data(self) -> Dict:
        """Get today's usage data."""
        today = get_today_date()
        return self.db.get(today, {})
    
    def get_app_today_data(self, package: str) -> Optional[Dict]:
        """Get today's data for specific app."""
        today_data = self.get_today_data()
        return today_data.get(package)
    
    def update_app_usage(self, package: str, used_minutes: int) -> bool:
        """Update app usage in database."""
        today = get_today_date()
        
        if today not in self.db:
            self.db[today] = {}
        
        app_data = self.config["apps"].get(package)
        if not app_data:
            return False
        
        if package not in self.db[today]:
            self.db[today][package] = {
                "name": app_data["name"],
                "total_minutes_used": 0,
                "limit_minutes": app_data["limit_minutes"],
                "remaining_minutes": app_data["limit_minutes"],
                "sessions": [],
                "limit_reached": False,
                "blocked_at": None,
            }
        
        today_app = self.db[today][package]
        today_app["total_minutes_used"] = used_minutes
        today_app["remaining_minutes"] = max(0, app_data["limit_minutes"] - used_minutes)
        
        self.save_db()
        return True
    
    def mark_limit_reached(self, package: str) -> bool:
        """Mark that app's limit has been reached."""
        today = get_today_date()
        
        if today not in self.db or package not in self.db[today]:
            return False
        
        self.db[today][package]["limit_reached"] = True
        self.db[today][package]["blocked_at"] = datetime.now().isoformat()
        
        self.save_db()
        log_message(f"Limit reached for {package}")
        return True
    
    def record_session(self, package: str, start_time: str, end_time: str, 
                       duration_minutes: int) -> bool:
        """Record a usage session for an app."""
        today = get_today_date()
        
        if today not in self.db or package not in self.db[today]:
            return False
        
        session = {
            "start": start_time,
            "end": end_time,
            "duration": duration_minutes,
        }
        
        self.db[today][package]["sessions"].append(session)
        self.save_db()
        return True
    
    def reset_app_timer(self, package: str) -> bool:
        """Reset timer for specific app."""
        today = get_today_date()
        
        if today not in self.db:
            self.db[today] = {}
        
        app_data = self.config["apps"].get(package)
        if not app_data or not app_data["enabled"]:
            return False
        
        self.db[today][package] = {
            "name": app_data["name"],
            "total_minutes_used": 0,
            "limit_minutes": app_data["limit_minutes"],
            "remaining_minutes": app_data["limit_minutes"],
            "sessions": [],
            "limit_reached": False,
            "blocked_at": None,
        }
        
        self.save_db()
        log_message(f"Reset timer for {package}")
        return True
    
    def reset_all_timers(self) -> int:
        """Reset all monitored apps. Returns count of reset apps."""
        count = 0
        for package, app_data in self.config["apps"].items():
            if app_data["enabled"] and self.reset_app_timer(package):
                count += 1
        
        self.config["last_reset_date"] = get_today_date()
        self.save_config()
        log_message(f"Reset all timers ({count} apps)")
        return count
    
    def check_and_reset_daily(self) -> bool:
        """Check if daily reset needed and perform it."""
        today = get_today_date()
        last_reset = self.config.get("last_reset_date")
        
        if last_reset != today:
            self.reset_all_timers()
            return True
        
        return False
    
    # ========== STATISTICS ==========
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """Get stats for specific day."""
        if date is None:
            date = get_today_date()
        
        return self.db.get(date, {})
    
    def get_total_usage(self, package: str, date: Optional[str] = None) -> int:
        """Get total usage in minutes for app on specific day."""
        if date is None:
            date = get_today_date()
        
        day_data = self.db.get(date, {})
        app_data = day_data.get(package, {})
        return app_data.get("total_minutes_used", 0)
    
    def get_remaining_time(self, package: str, date: Optional[str] = None) -> int:
        """Get remaining time for app."""
        if date is None:
            date = get_today_date()
        
        day_data = self.db.get(date, {})
        app_data = day_data.get(package, {})
        return max(0, app_data.get("remaining_minutes", 0))
    
    def is_limit_reached_today(self, package: str) -> bool:
        """Check if app limit reached today."""
        today_data = self.get_today_data()
        app_data = today_data.get(package, {})
        return app_data.get("limit_reached", False)
