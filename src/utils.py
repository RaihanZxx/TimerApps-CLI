"""Utility functions for TimerApps-CLI."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
from .exceptions import ValidationError


TIMERAPPS_DIR: Path = Path.home() / ".timerapps"


def ensure_timerapps_dir() -> Path:
    """Create ~/.timerapps directory if not exists.
    
    Returns:
        Path: The TimerApps configuration directory.
    """
    TIMERAPPS_DIR.mkdir(parents=True, exist_ok=True)
    return TIMERAPPS_DIR


def get_config_path() -> Path:
    """Get path to config.json.
    
    Returns:
        Path: Full path to configuration file.
    """
    return ensure_timerapps_dir() / "config.json"


def get_db_path() -> Path:
    """Get path to db.json.
    
    Returns:
        Path: Full path to database file.
    """
    return ensure_timerapps_dir() / "db.json"


def get_log_path() -> Path:
    """Get path to logs.log.
    
    Returns:
        Path: Full path to log file.
    """
    return ensure_timerapps_dir() / "logs.log"


def log_message(message: str, level: str = "INFO") -> None:
    """Log message to file with timestamp.
    
    Args:
        message: The message to log.
        level: Log level (INFO, WARN, ERROR, DEBUG).
    """
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry: str = f"[{timestamp}] [{level}] {message}\n"
    
    with open(get_log_path(), "a") as f:
        f.write(log_entry)


def get_today_date() -> str:
    """Get today's date as YYYY-MM-DD.
    
    Returns:
        str: Current date in YYYY-MM-DD format.
    """
    return datetime.now().strftime("%Y-%m-%d")


def minutes_to_seconds(minutes: int) -> int:
    """Convert minutes to seconds.
    
    Args:
        minutes: Number of minutes to convert.
        
    Returns:
        int: Equivalent number of seconds.
    """
    return minutes * 60


def seconds_to_minutes(seconds: int) -> int:
    """Convert seconds to minutes (rounded down).
    
    Args:
        seconds: Number of seconds to convert.
        
    Returns:
        int: Equivalent number of minutes (truncated).
    """
    return int(seconds / 60)


def format_time(minutes: int) -> str:
    """Format minutes to human-readable time string.
    
    Args:
        minutes: Number of minutes to format.
        
    Returns:
        str: Human-readable time string (e.g., "1h 30m", "45m").
    """
    hours: int = minutes // 60
    mins: int = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def get_progress_bar(used: int, limit: int, width: int = 20) -> str:
    """Get progress bar string.
    
    Args:
        used: Amount used/elapsed.
        limit: Total limit/capacity.
        width: Width of progress bar in characters (default 20).
        
    Returns:
        str: Progress bar visualization (filled█ and empty░ blocks).
    """
    if limit == 0:
        return "█" * width
    
    filled: int = int((used / limit) * width)
    filled = min(filled, width)
    empty: int = width - filled
    
    return "█" * filled + "░" * empty


def is_valid_package_name(package: str) -> bool:
    """Check if string is valid Android package name.
    
    Args:
        package: Package name to validate.
        
    Returns:
        bool: True if valid Android package format (com.xxx.yyy), False otherwise.
    """
    parts: list[str] = package.split(".")
    return len(parts) >= 2 and all(p.isalnum() for p in parts)


def dict_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries (updates override base).
    
    Args:
        base: Base dictionary to merge into.
        updates: Dictionary with updates/overrides.
        
    Returns:
        Dict: Merged dictionary with updates applied recursively.
    """
    result: Dict[str, Any] = base.copy()
    for key, value in updates.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = dict_merge(result[key], value)
        else:
            result[key] = value
    return result


def validate_package_name(package: str) -> str:
    """Validate and return Android package name.
    
    Args:
        package: Package name to validate.
        
    Returns:
        str: Validated package name.
        
    Raises:
        ValidationError: If package name is invalid.
    """
    if not package or not isinstance(package, str):
        raise ValidationError("Package name must be a non-empty string")
    
    package = package.strip()
    
    if not is_valid_package_name(package):
        raise ValidationError(f"Invalid package name: {package}. Must be in format com.example.app")
    
    return package


def validate_limit_minutes(minutes: Any) -> int:
    """Validate and return app limit in minutes.
    
    Args:
        minutes: Minutes value to validate.
        
    Returns:
        int: Validated minute limit.
        
    Raises:
        ValidationError: If limit is invalid.
    """
    try:
        limit: int = int(minutes)
    except (ValueError, TypeError):
        raise ValidationError(f"Limit must be a positive integer, got: {minutes}")
    
    if limit <= 0:
        raise ValidationError(f"Limit must be greater than 0, got: {limit}")
    
    if limit > 1440:  # 24 hours
        raise ValidationError(f"Limit cannot exceed 24 hours (1440 minutes), got: {limit}")
    
    return limit


def validate_app_name(name: str) -> str:
    """Validate and return app display name.
    
    Args:
        name: App name to validate.
        
    Returns:
        str: Validated app name.
        
    Raises:
        ValidationError: If app name is invalid.
    """
    if not name or not isinstance(name, str):
        raise ValidationError("App name must be a non-empty string")
    
    name = name.strip()
    
    if len(name) > 100:
        raise ValidationError(f"App name too long (max 100 chars), got {len(name)} chars")
    
    return name


def validate_action(action: str) -> str:
    """Validate app action (kill or freeze).
    
    Args:
        action: Action to validate.
        
    Returns:
        str: Validated action.
        
    Raises:
        ValidationError: If action is invalid.
    """
    valid_actions = ["kill", "freeze"]
    
    if action not in valid_actions:
        raise ValidationError(f"Invalid action: {action}. Must be one of: {', '.join(valid_actions)}")
    
    return action
