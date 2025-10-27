"""Comprehensive test suite for ConfigManager."""

import pytest
from src.config_manager import ConfigManager
from src.utils import get_today_date


class TestConfigManagerAppOperations:
    """Test app CRUD operations."""

    def test_add_app_success(self, config_manager):
        """Test adding a new app."""
        result = config_manager.add_app("com.test.app", "Test App", 60, "kill")
        assert result is True
        assert "com.test.app" in config_manager.get_all_apps()

    def test_add_app_duplicate(self, config_manager):
        """Test adding duplicate app returns False."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.add_app("com.test.app", "Test App 2", 90)
        assert result is False

    def test_add_app_creates_db_entry(self, config_manager):
        """Test that adding app creates database entry."""
        config_manager.add_app("com.test.app", "Test App", 60)
        today = get_today_date()
        assert today in config_manager.db
        assert "com.test.app" in config_manager.db[today]

    def test_remove_app_success(self, config_manager):
        """Test removing an app."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.remove_app("com.test.app")
        assert result is True
        assert "com.test.app" not in config_manager.get_all_apps()

    def test_remove_app_nonexistent(self, config_manager):
        """Test removing non-existent app returns False."""
        result = config_manager.remove_app("com.nonexistent.app")
        assert result is False

    def test_get_app_returns_app_data(self, config_manager):
        """Test retrieving app configuration."""
        config_manager.add_app("com.test.app", "Test App", 60, "freeze")
        app = config_manager.get_app("com.test.app")
        assert app is not None
        assert app["name"] == "Test App"
        assert app["limit_minutes"] == 60
        assert app["action"] == "freeze"

    def test_get_app_nonexistent(self, config_manager):
        """Test getting non-existent app returns None."""
        app = config_manager.get_app("com.nonexistent.app")
        assert app is None

    def test_enable_disable_app(self, config_manager):
        """Test enabling/disabling app monitoring."""
        config_manager.add_app("com.test.app", "Test App", 60)
        
        # Disable
        result = config_manager.enable_app("com.test.app", False)
        assert result is True
        assert config_manager.get_app("com.test.app")["enabled"] is False
        
        # Enable
        result = config_manager.enable_app("com.test.app", True)
        assert result is True
        assert config_manager.get_app("com.test.app")["enabled"] is True

    def test_update_app_limit(self, config_manager):
        """Test updating app time limit."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.update_app_limit("com.test.app", 120)
        assert result is True
        assert config_manager.get_app("com.test.app")["limit_minutes"] == 120

    def test_update_app_action(self, config_manager):
        """Test updating app action (kill/freeze)."""
        config_manager.add_app("com.test.app", "Test App", 60, "kill")
        result = config_manager.update_app_action("com.test.app", "freeze")
        assert result is True
        assert config_manager.get_app("com.test.app")["action"] == "freeze"

    def test_update_app_name(self, config_manager):
        """Test updating app display name."""
        config_manager.add_app("com.test.app", "Old Name", 60)
        result = config_manager.update_app_name("com.test.app", "New Name")
        assert result is True
        assert config_manager.get_app("com.test.app")["name"] == "New Name"


class TestConfigManagerUsageTracking:
    """Test app usage tracking operations."""

    def test_update_app_usage(self, config_manager):
        """Test updating app usage in database."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.update_app_usage("com.test.app", 30)
        assert result is True
        
        today = get_today_date()
        assert config_manager.db[today]["com.test.app"]["total_minutes_used"] == 30
        assert config_manager.db[today]["com.test.app"]["remaining_minutes"] == 30

    def test_get_total_usage(self, config_manager):
        """Test retrieving total usage."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 45)
        
        usage = config_manager.get_total_usage("com.test.app")
        assert usage == 45

    def test_get_remaining_time(self, config_manager):
        """Test calculating remaining time."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 35)
        
        remaining = config_manager.get_remaining_time("com.test.app")
        assert remaining == 25

    def test_get_remaining_time_exceeds_limit(self, config_manager):
        """Test remaining time when usage exceeds limit."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 100)
        
        remaining = config_manager.get_remaining_time("com.test.app")
        assert remaining == 0

    def test_mark_limit_reached(self, config_manager):
        """Test marking app limit as reached."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.mark_limit_reached("com.test.app")
        assert result is True
        
        today = get_today_date()
        assert config_manager.db[today]["com.test.app"]["limit_reached"] is True
        assert config_manager.db[today]["com.test.app"]["blocked_at"] is not None

    def test_is_limit_reached_today(self, config_manager):
        """Test checking if limit was reached today."""
        config_manager.add_app("com.test.app", "Test App", 60)
        assert config_manager.is_limit_reached_today("com.test.app") is False
        
        config_manager.mark_limit_reached("com.test.app")
        assert config_manager.is_limit_reached_today("com.test.app") is True

    def test_record_session(self, config_manager):
        """Test recording a usage session."""
        config_manager.add_app("com.test.app", "Test App", 60)
        result = config_manager.record_session("com.test.app", "09:00", "09:15", 15)
        assert result is True
        
        today = get_today_date()
        sessions = config_manager.db[today]["com.test.app"]["sessions"]
        assert len(sessions) == 1
        assert sessions[0]["duration"] == 15


class TestConfigManagerResets:
    """Test timer reset operations."""

    def test_reset_app_timer(self, config_manager):
        """Test resetting a single app timer."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 45)
        
        result = config_manager.reset_app_timer("com.test.app")
        assert result is True
        assert config_manager.get_total_usage("com.test.app") == 0

    def test_reset_all_timers(self, config_manager):
        """Test resetting all app timers."""
        config_manager.add_app("com.app1", "App 1", 60)
        config_manager.add_app("com.app2", "App 2", 30)
        config_manager.update_app_usage("com.app1", 50)
        config_manager.update_app_usage("com.app2", 25)
        
        count = config_manager.reset_all_timers()
        assert count == 2
        assert config_manager.get_total_usage("com.app1") == 0
        assert config_manager.get_total_usage("com.app2") == 0

    def test_reset_only_enabled_apps(self, config_manager):
        """Test that reset only affects enabled apps."""
        config_manager.add_app("com.app1", "App 1", 60, enabled=True)
        config_manager.add_app("com.app2", "App 2", 30, enabled=False)
        config_manager.update_app_usage("com.app1", 50)
        config_manager.update_app_usage("com.app2", 25)
        
        count = config_manager.reset_all_timers()
        assert count == 1
        assert config_manager.get_total_usage("com.app1") == 0
        # Disabled app should not be reset
        assert config_manager.get_total_usage("com.app2") == 25

    def test_check_and_reset_daily(self, config_manager):
        """Test daily auto-reset check."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 45)
        
        # First call should reset
        result = config_manager.check_and_reset_daily()
        assert result is True
        assert config_manager.get_total_usage("com.test.app") == 0
        
        # Second call same day should not reset
        result = config_manager.check_and_reset_daily()
        assert result is False


class TestConfigManagerPersistence:
    """Test config and database persistence."""

    def test_config_saved_to_file(self, config_manager, mock_config_paths):
        """Test that config is saved to JSON file."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.save_config()
        
        config_file = mock_config_paths / "config.json"
        assert config_file.exists()

    def test_db_saved_to_file(self, config_manager, mock_config_paths):
        """Test that database is saved to JSON file."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.save_db()
        
        db_file = mock_config_paths / "db.json"
        assert db_file.exists()

    def test_reload_config(self, config_manager, mock_config_paths):
        """Test reloading config from file."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.save_config()
        
        # Create new instance to load from file
        new_manager = ConfigManager()
        assert "com.test.app" in new_manager.get_all_apps()

    def test_reload_database(self, config_manager, mock_config_paths):
        """Test reloading database from file."""
        config_manager.add_app("com.test.app", "Test App", 60)
        config_manager.update_app_usage("com.test.app", 30)
        config_manager.save_db()
        
        # Create new instance to load from file
        new_manager = ConfigManager()
        today = get_today_date()
        assert new_manager.db[today]["com.test.app"]["total_minutes_used"] == 30


class TestConfigManagerDevice:
    """Test device configuration."""

    def test_set_get_device_rooted(self, config_manager):
        """Test setting and getting device root status."""
        config_manager.set_device_rooted(True)
        assert config_manager.get_device_rooted() is True
        
        config_manager.set_device_rooted(False)
        assert config_manager.get_device_rooted() is False

    def test_set_device_rooted_updates_adb_flag(self, config_manager):
        """Test that setting rooted status updates ADB flag."""
        config_manager.set_device_rooted(True)
        assert config_manager.config["device"]["use_adb"] is False
        
        config_manager.set_device_rooted(False)
        assert config_manager.config["device"]["use_adb"] is True
