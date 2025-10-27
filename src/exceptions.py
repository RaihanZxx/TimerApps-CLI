"""Custom exceptions for TimerApps-CLI."""


class TimerAppsException(Exception):
    """Base exception for all TimerApps errors."""
    pass


class ConfigError(TimerAppsException):
    """Raised when config operations fail."""
    pass


class DatabaseError(TimerAppsException):
    """Raised when database operations fail."""
    pass


class DeviceError(TimerAppsException):
    """Raised when device/ADB operations fail."""
    pass


class ValidationError(TimerAppsException):
    """Raised when validation fails (input validation, package name, etc)."""
    pass


class NotificationError(TimerAppsException):
    """Raised when notification operations fail."""
    pass


class DaemonError(TimerAppsException):
    """Raised when daemon operations fail."""
    pass
