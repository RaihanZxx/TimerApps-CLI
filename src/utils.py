import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


TIMERAPPS_DIR = Path.home() / ".timerapps"


def ensure_timerapps_dir() -> Path:
    """Create ~/.timerapps directory if not exists."""
    TIMERAPPS_DIR.mkdir(parents=True, exist_ok=True)
    return TIMERAPPS_DIR


def get_config_path() -> Path:
    """Get path to config.json."""
    return ensure_timerapps_dir() / "config.json"


def get_db_path() -> Path:
    """Get path to db.json."""
    return ensure_timerapps_dir() / "db.json"


def get_log_path() -> Path:
    """Get path to logs.log."""
    return ensure_timerapps_dir() / "logs.log"


def log_message(message: str, level: str = "INFO") -> None:
    """Log message to file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    with open(get_log_path(), "a") as f:
        f.write(log_entry)


def get_today_date() -> str:
    """Get today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def minutes_to_seconds(minutes: int) -> int:
    """Convert minutes to seconds."""
    return minutes * 60


def seconds_to_minutes(seconds: int) -> int:
    """Convert seconds to minutes (rounded down)."""
    return int(seconds / 60)


def format_time(minutes: int) -> str:
    """Format minutes to human-readable time string."""
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def get_progress_bar(used: int, limit: int, width: int = 20) -> str:
    """Get progress bar string."""
    if limit == 0:
        return "█" * width
    
    filled = int((used / limit) * width)
    filled = min(filled, width)
    empty = width - filled
    
    return "█" * filled + "░" * empty


def is_valid_package_name(package: str) -> bool:
    """Check if string is valid Android package name."""
    # Basic validation: com.example.app format
    parts = package.split(".")
    return len(parts) >= 2 and all(p.isalnum() for p in parts)


def dict_merge(base: Dict, updates: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in updates.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = dict_merge(result[key], value)
        else:
            result[key] = value
    return result
