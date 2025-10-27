"""Comprehensive test suite for AppMonitor."""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from src.app_monitor import AppMonitor, TimerState
from src.utils import get_today_date


class TestAppMonitorInitialization:
    """Test AppMonitor initialization."""

    def test_app_monitor_init(self, config_manager, mock_adb_handler, mock_notification_manager):
        """Test AppMonitor initialization."""
        monitor = AppMonitor(config_manager, mock_adb_handler, mock_notification_manager)
        assert monitor._running is False
        assert monitor._thread is None
        assert len(monitor._app_states) == 0

    def test_app_monitor_init_with_apps(self, populated_config_manager, mock_adb_handler, mock_notification_manager):
        """Test AppMonitor with pre-populated apps."""
        monitor = AppMonitor(populated_config_manager, mock_adb_handler, mock_notification_manager)
        
        # Should initialize tracking for enabled apps
        monitor._initialize_app_state("com.instagram.android")
        assert "com.instagram.android" in monitor._app_states


class TestAppMonitorStateManagement:
    """Test app state management."""

    def test_get_app_state_inactive(self, app_monitor, config_manager):
        """Test getting initial app state (inactive)."""
        config_manager.add_app("com.test.app", "Test App", 60)
        state = app_monitor.get_app_state("com.test.app")
        assert state == TimerState.INACTIVE

    def test_initialize_app_state(self, app_monitor, config_manager):
        """Test app state initialization."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._initialize_app_state("com.test.app")
        
        assert "com.test.app" in app_monitor._app_states
        assert app_monitor._app_states["com.test.app"] == TimerState.INACTIVE

    def test_app_state_persistence_in_memory(self, app_monitor, config_manager):
        """Test that app state persists in memory."""
        config_manager.add_app("com.test.app", "Test App", 60)
        
        state1 = app_monitor.get_app_state("com.test.app")
        state2 = app_monitor.get_app_state("com.test.app")
        
        assert state1 == state2


class TestAppMonitorUsageTracking:
    """Test usage time tracking."""

    def test_get_app_used_time_zero(self, app_monitor, config_manager):
        """Test getting used time for new app."""
        config_manager.add_app("com.test.app", "Test App", 60)
        used = app_monitor.get_app_used_minutes("com.test.app")
        assert used == 0

    def test_get_app_used_minutes_conversion(self, app_monitor, config_manager):
        """Test seconds to minutes conversion."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_total_seconds["com.test.app"] = 125  # 2 minutes 5 seconds
        
        used = app_monitor.get_app_used_minutes("com.test.app")
        assert used == 2

    def test_update_total_usage_saves_to_db(self, app_monitor, config_manager):
        """Test that total usage is saved to database."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_total_seconds["com.test.app"] = 1800  # 30 minutes
        
        app_monitor._update_total_usage()
        
        today = get_today_date()
        assert config_manager.db[today]["com.test.app"]["total_minutes_used"] == 30

    def test_get_all_app_times(self, app_monitor, config_manager):
        """Test getting all app times at once."""
        config_manager.add_app("com.app1", "App 1", 60)
        config_manager.add_app("com.app2", "App 2", 30)
        app_monitor._app_total_seconds["com.app1"] = 1200  # 20 min
        app_monitor._app_total_seconds["com.app2"] = 600   # 10 min
        
        times = app_monitor.get_all_app_times()
        assert times["com.app1"] == 20
        assert times["com.app2"] == 10


class TestAppMonitorResets:
    """Test timer reset functionality."""

    def test_reset_app_single(self, app_monitor, config_manager):
        """Test resetting a single app timer."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_total_seconds["com.test.app"] = 1200  # 20 min
        
        result = app_monitor.reset_app("com.test.app")
        assert result is True
        assert app_monitor._app_total_seconds["com.test.app"] == 0
        assert app_monitor._app_states["com.test.app"] == TimerState.INACTIVE

    def test_reset_all_apps(self, app_monitor, config_manager):
        """Test resetting all app timers."""
        config_manager.add_app("com.app1", "App 1", 60)
        config_manager.add_app("com.app2", "App 2", 30)
        app_monitor._app_total_seconds["com.app1"] = 1200
        app_monitor._app_total_seconds["com.app2"] = 900
        
        count = app_monitor.reset_all()
        assert count == 2
        assert app_monitor._app_total_seconds["com.app1"] == 0
        assert app_monitor._app_total_seconds["com.app2"] == 0

    def test_reset_nonexistent_app(self, app_monitor, config_manager):
        """Test resetting non-existent app."""
        result = app_monitor.reset_app("com.nonexistent.app")
        assert result is False


class TestAppMonitorMonitoring:
    """Test monitoring start/stop."""

    def test_monitor_start(self, app_monitor):
        """Test starting the monitor."""
        app_monitor.start()
        assert app_monitor._running is True
        assert app_monitor._thread is not None
        app_monitor.stop()

    def test_monitor_stop(self, app_monitor):
        """Test stopping the monitor."""
        app_monitor.start()
        time.sleep(0.1)  # Let it run briefly
        app_monitor.stop()
        assert app_monitor._running is False

    def test_monitor_is_running(self, app_monitor):
        """Test checking if monitor is running."""
        assert app_monitor.is_running() is False
        app_monitor.start()
        assert app_monitor.is_running() is True
        app_monitor.stop()
        assert app_monitor.is_running() is False

    def test_monitor_double_start(self, app_monitor):
        """Test that starting monitor twice doesn't create multiple threads."""
        app_monitor.start()
        thread1 = app_monitor._thread
        
        app_monitor.start()  # Second start should be ignored
        thread2 = app_monitor._thread
        
        assert thread1 is thread2
        app_monitor.stop()

    def test_monitor_stop_without_start(self, app_monitor):
        """Test stopping monitor that wasn't started."""
        result = app_monitor.stop()  # Should not raise
        assert app_monitor._running is False


class TestAppMonitorThreadSafety:
    """Test thread safety and concurrent operations."""

    def test_concurrent_app_state_access(self, app_monitor, config_manager):
        """Test concurrent access to app states."""
        config_manager.add_app("com.test.app", "Test App", 60)
        
        def access_state():
            for _ in range(100):
                app_monitor.get_app_state("com.test.app")
        
        threads = [threading.Thread(target=access_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

    def test_concurrent_usage_tracking(self, app_monitor, config_manager):
        """Test concurrent usage updates."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._initialize_app_state("com.test.app")
        
        def update_usage():
            for _ in range(10):
                app_monitor._update_total_usage()
        
        threads = [threading.Thread(target=update_usage) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

    def test_concurrent_reset(self, app_monitor, config_manager):
        """Test concurrent reset operations."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_total_seconds["com.test.app"] = 1200
        
        def reset():
            app_monitor.reset_app("com.test.app")
        
        threads = [threading.Thread(target=reset) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
        
        # Should be safe even if called multiple times
        assert app_monitor._app_total_seconds["com.test.app"] == 0


class TestAppMonitorEnforcement:
    """Test limit enforcement."""

    def test_enforce_limit_kill_action(self, app_monitor, config_manager, mock_adb_handler):
        """Test enforcing limit with kill action."""
        config_manager.add_app("com.test.app", "Test App", 60, action="kill")
        app_monitor._app_states["com.test.app"] = TimerState.MONITORING
        
        app_monitor._enforce_limit("com.test.app", config_manager.get_app("com.test.app"))
        
        mock_adb_handler.kill_app.assert_called_with("com.test.app")
        assert app_monitor._app_states["com.test.app"] == TimerState.BLOCKED

    def test_enforce_limit_freeze_action(self, app_monitor, config_manager, mock_adb_handler):
        """Test enforcing limit with freeze action."""
        config_manager.add_app("com.test.app", "Test App", 60, action="freeze")
        app_monitor._app_states["com.test.app"] = TimerState.MONITORING
        
        app_monitor._enforce_limit("com.test.app", config_manager.get_app("com.test.app"))
        
        mock_adb_handler.freeze_app.assert_called_with("com.test.app")
        assert app_monitor._app_states["com.test.app"] == TimerState.BLOCKED

    def test_enforce_limit_already_blocked(self, app_monitor, config_manager):
        """Test that enforcing on already blocked app is idempotent."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_states["com.test.app"] = TimerState.BLOCKED
        
        # Should do nothing
        app_monitor._enforce_limit("com.test.app", config_manager.get_app("com.test.app"))
        
        # Should still be blocked
        assert app_monitor._app_states["com.test.app"] == TimerState.BLOCKED


class TestAppMonitorIntegration:
    """Integration tests for AppMonitor."""

    def test_monitor_lifecycle(self, app_monitor, config_manager):
        """Test full monitoring lifecycle."""
        config_manager.add_app("com.test.app", "Test App", 60)
        
        # Start
        app_monitor.start()
        assert app_monitor.is_running()
        
        # Let it run briefly
        time.sleep(0.2)
        
        # Stop
        app_monitor.stop()
        assert not app_monitor.is_running()

    def test_monitor_manual_usage_update(self, app_monitor, config_manager):
        """Test that monitor updates usage in database."""
        config_manager.add_app("com.test.app", "Test App", 60)
        app_monitor._app_total_seconds["com.test.app"] = 600
        
        # Manually call update function
        app_monitor._update_total_usage()
        
        # Data should be saved
        today = get_today_date()
        saved_minutes = config_manager.db[today]["com.test.app"]["total_minutes_used"]
        assert saved_minutes == 10
