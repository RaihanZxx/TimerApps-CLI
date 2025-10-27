"""Pytest configuration and fixtures for TimerApps-CLI tests."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager, DEFAULT_CONFIG
from src.adb_handler import ADBHandler
from src.app_monitor import AppMonitor
from src.notifications import NotificationManager
from src.utils import get_today_date


@pytest.fixture
def temp_timerapps_dir(tmp_path):
    """Create temporary TimerApps directory structure."""
    timerapps_dir = tmp_path / ".timerapps"
    timerapps_dir.mkdir(parents=True, exist_ok=True)
    return timerapps_dir


@pytest.fixture
def mock_config_paths(temp_timerapps_dir, monkeypatch):
    """Mock config and database paths to use temporary directory."""
    def mock_get_config_path():
        return temp_timerapps_dir / "config.json"
    
    def mock_get_db_path():
        return temp_timerapps_dir / "db.json"
    
    def mock_get_log_path():
        return temp_timerapps_dir / "logs.log"
    
    def mock_ensure_timerapps_dir():
        temp_timerapps_dir.mkdir(parents=True, exist_ok=True)
        return temp_timerapps_dir
    
    monkeypatch.setattr("src.utils.get_config_path", mock_get_config_path)
    monkeypatch.setattr("src.utils.get_db_path", mock_get_db_path)
    monkeypatch.setattr("src.utils.get_log_path", mock_get_log_path)
    monkeypatch.setattr("src.utils.ensure_timerapps_dir", mock_ensure_timerapps_dir)
    
    return temp_timerapps_dir


@pytest.fixture
def config_manager(mock_config_paths):
    """Create a ConfigManager instance with mocked paths."""
    mgr = ConfigManager()
    yield mgr
    # Cleanup: ensure db is cleared between tests
    mgr.db.clear()
    mgr.config["apps"].clear()
    mgr.save_db()
    mgr.save_config()


@pytest.fixture
def sample_app_config():
    """Sample app configuration."""
    return {
        "name": "Instagram",
        "limit_minutes": 60,
        "enabled": True,
        "action": "kill",
    }


@pytest.fixture
def mock_adb_handler():
    """Create a mock ADBHandler."""
    handler = Mock(spec=ADBHandler)
    handler.use_root = False
    handler.device_id = "emulator-5554"
    handler.is_available = True
    handler.get_active_app = Mock(return_value=None)
    handler.get_installed_apps = Mock(return_value=[])
    handler.get_app_name = Mock(return_value="Test App")
    handler.kill_app = Mock(return_value=True)
    handler.freeze_app = Mock(return_value=True)
    handler.unfreeze_app = Mock(return_value=True)
    handler.is_app_running = Mock(return_value=False)
    handler.detect_root = Mock(return_value=False)
    return handler


@pytest.fixture
def mock_notification_manager():
    """Create a mock NotificationManager."""
    manager = Mock(spec=NotificationManager)
    manager.enabled = True
    manager.send_limit_reached = Mock(return_value=True)
    manager.send_warning = Mock(return_value=True)
    manager.send_limit_reset = Mock(return_value=True)
    manager.send_custom = Mock(return_value=True)
    manager.send_monitoring_started = Mock(return_value=True)
    manager.send_monitoring_stopped = Mock(return_value=True)
    return manager


@pytest.fixture
def app_monitor(config_manager, mock_adb_handler, mock_notification_manager):
    """Create an AppMonitor instance with mocked dependencies."""
    # Set device as rooted in config
    config_manager.set_device_rooted(False)
    
    monitor = AppMonitor(config_manager, mock_adb_handler, mock_notification_manager)
    yield monitor
    
    # Cleanup: stop monitor if running
    if monitor.is_running():
        monitor.stop()


@pytest.fixture
def populated_config_manager(config_manager, sample_app_config):
    """ConfigManager with some apps already added."""
    config_manager.add_app("com.instagram.android", "Instagram", 60, "kill", enabled=True)
    config_manager.add_app("com.tiktok.android", "TikTok", 30, "freeze", enabled=True)
    config_manager.add_app("com.youtube.com", "YouTube", 90, "kill", enabled=False)
    return config_manager


@pytest.fixture
def monkeypatch_subprocess():
    """Fixture to patch subprocess for safe command execution testing."""
    with patch("subprocess.run") as mock_run:
        # Default successful response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="success",
            stderr=""
        )
        yield mock_run
