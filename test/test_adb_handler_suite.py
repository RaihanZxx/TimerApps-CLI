"""Comprehensive test suite for ADBHandler."""

import pytest
from unittest.mock import Mock, patch, call, MagicMock
import subprocess
from src.adb_handler import ADBHandler


class TestADBHandlerInitialization:
    """Test ADBHandler initialization and device detection."""

    @patch("subprocess.run")
    def test_adb_handler_init_with_device(self, mock_run):
        """Test ADBHandler initializes and detects device."""
        mock_run.return_value = MagicMock(
            stdout="List of attached devices\nemulator-5554  device\n",
            returncode=0
        )
        
        handler = ADBHandler(use_root=False)
        assert handler.device_id == "emulator-5554"
        assert handler.is_available is True

    @patch("subprocess.run")
    def test_adb_handler_init_no_device(self, mock_run):
        """Test ADBHandler when no device is connected."""
        mock_run.return_value = MagicMock(
            stdout="List of attached devices\n",
            returncode=0
        )
        
        handler = ADBHandler(use_root=False)
        assert handler.device_id is None
        assert handler.is_available is False

    @patch("subprocess.run")
    def test_adb_handler_init_root_mode(self, mock_run):
        """Test ADBHandler in root mode."""
        # For root mode, detect_device doesn't run
        handler = ADBHandler(use_root=True)
        assert handler.use_root is True


class TestADBHandlerGetActiveApp:
    """Test getting currently active app."""

    @patch.object(ADBHandler, "_adb_shell")
    def test_get_active_app_success(self, mock_adb_shell):
        """Test retrieving active app package name."""
        mock_adb_shell.return_value = (
            True,
            "    mCurrentFocus=Window{7c8f8b0 u0 com.instagram.android/com.instagram.android.MainActivity}"
        )
        
        handler = ADBHandler(use_root=False)
        active = handler.get_active_app()
        assert active == "com.instagram.android"

    @patch.object(ADBHandler, "_adb_shell")
    def test_get_active_app_fallback_to_window(self, mock_adb_shell):
        """Test fallback from activity to window focus."""
        mock_adb_shell.side_effect = [
            (False, ""),  # First call (activity) fails
            (True, "    mCurrentFocus=Window{abc u0 com.tiktok.android/com.tiktok.android.MainActivity}")
        ]
        
        handler = ADBHandler(use_root=False)
        active = handler.get_active_app()
        assert active == "com.tiktok.android"

    @patch.object(ADBHandler, "_adb_shell")
    def test_get_active_app_no_app_running(self, mock_adb_shell):
        """Test when no app is focused."""
        mock_adb_shell.side_effect = [
            (False, ""),
            (False, "")
        ]
        
        handler = ADBHandler(use_root=False)
        active = handler.get_active_app()
        assert active is None


class TestADBHandlerGetInstalledApps:
    """Test getting installed apps list."""

    @patch.object(ADBHandler, "_adb_shell")
    @patch.object(ADBHandler, "get_app_name")
    def test_get_installed_apps(self, mock_get_name, mock_adb_shell):
        """Test retrieving list of installed apps."""
        mock_adb_shell.return_value = (
            True,
            "package:com.instagram.android\npackage:com.tiktok.android\npackage:com.youtube.com"
        )
        mock_get_name.side_effect = ["Instagram", "TikTok", "YouTube"]
        
        handler = ADBHandler(use_root=False)
        apps = handler.get_installed_apps()
        
        assert len(apps) == 3
        assert apps[0]["package"] == "com.instagram.android"
        assert apps[0]["name"] == "Instagram"

    @patch.object(ADBHandler, "_adb_shell")
    def test_get_installed_apps_failure(self, mock_adb_shell):
        """Test handling when app list retrieval fails."""
        mock_adb_shell.return_value = (False, "")
        
        handler = ADBHandler(use_root=False)
        apps = handler.get_installed_apps()
        
        assert apps == []


class TestADBHandlerAppControl:
    """Test app control operations (kill, freeze, unfreeze)."""

    @patch.object(ADBHandler, "_adb_shell")
    def test_kill_app_success(self, mock_adb_shell):
        """Test force-stopping an app."""
        mock_adb_shell.return_value = (True, "")
        
        handler = ADBHandler(use_root=False)
        result = handler.kill_app("com.test.app")
        
        assert result is True
        mock_adb_shell.assert_called_once_with("am force-stop com.test.app")

    @patch.object(ADBHandler, "_adb_shell")
    def test_kill_app_failure(self, mock_adb_shell):
        """Test handling when kill fails."""
        mock_adb_shell.return_value = (False, "Permission denied")
        
        handler = ADBHandler(use_root=False)
        result = handler.kill_app("com.test.app")
        
        assert result is False

    @patch.object(ADBHandler, "_adb_shell")
    def test_freeze_app_success(self, mock_adb_shell):
        """Test disabling (freezing) an app."""
        mock_adb_shell.return_value = (True, "")
        
        handler = ADBHandler(use_root=False)
        result = handler.freeze_app("com.test.app")
        
        assert result is True
        mock_adb_shell.assert_called_once()

    @patch.object(ADBHandler, "_adb_shell")
    def test_unfreeze_app_success(self, mock_adb_shell):
        """Test re-enabling (unfreezing) an app."""
        mock_adb_shell.return_value = (True, "")
        
        handler = ADBHandler(use_root=False)
        result = handler.unfreeze_app("com.test.app")
        
        assert result is True
        mock_adb_shell.assert_called_once()

    @patch.object(ADBHandler, "_adb_shell")
    def test_is_app_running_true(self, mock_adb_shell):
        """Test checking if app is running (true case)."""
        mock_adb_shell.return_value = (True, "1234")  # PID
        
        handler = ADBHandler(use_root=False)
        result = handler.is_app_running("com.test.app")
        
        assert result is True

    @patch.object(ADBHandler, "_adb_shell")
    def test_is_app_running_false(self, mock_adb_shell):
        """Test checking if app is running (false case)."""
        mock_adb_shell.return_value = (True, "")  # No PID
        
        handler = ADBHandler(use_root=False)
        result = handler.is_app_running("com.test.app")
        
        assert result is False


class TestADBHandlerDetection:
    """Test device detection and root detection."""

    @patch("subprocess.run")
    def test_detect_root_success(self, mock_run):
        """Test detecting rooted device."""
        mock_run.return_value = MagicMock(returncode=0)
        
        handler = ADBHandler(use_root=False)
        result = handler.detect_root()
        
        assert result is True

    @patch("subprocess.run")
    def test_detect_root_failure(self, mock_run):
        """Test detecting non-rooted device."""
        mock_run.return_value = MagicMock(returncode=1)
        
        handler = ADBHandler(use_root=False)
        result = handler.detect_root()
        
        assert result is False


class TestADBHandlerErrorHandling:
    """Test error handling in ADBHandler."""

    @patch.object(ADBHandler, "_adb_shell")
    def test_adb_shell_timeout(self, mock_adb_shell):
        """Test handling of ADB shell timeout."""
        mock_adb_shell.side_effect = subprocess.TimeoutExpired("adb", 10)
        
        handler = ADBHandler(use_root=False)
        # Should handle gracefully
        result = handler.kill_app("com.test.app")
        
        assert result is False

    @patch.object(ADBHandler, "_adb_shell")
    def test_adb_shell_unauthorized(self, mock_adb_shell):
        """Test handling of unauthorized ADB device."""
        mock_adb_shell.return_value = (False, "unauthorized")
        
        handler = ADBHandler(use_root=False)
        result = handler.kill_app("com.test.app")
        
        assert result is False

    @patch.object(ADBHandler, "_adb_shell")
    def test_get_app_name_fallback(self, mock_adb_shell):
        """Test app name extraction fallback."""
        mock_adb_shell.return_value = (False, "")
        
        handler = ADBHandler(use_root=False)
        name = handler.get_app_name("com.example.app")
        
        # Should fallback to package name
        assert name == "App"


class TestADBHandlerCommandExecution:
    """Test low-level command execution."""

    @patch("subprocess.run")
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )
        
        handler = ADBHandler(use_root=False)
        success, output = handler._run_command(["test", "command"])
        
        assert success is True
        assert output == "output"

    @patch("subprocess.run")
    def test_run_command_failure(self, mock_run):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error"
        )
        
        handler = ADBHandler(use_root=False)
        success, output = handler._run_command(["test", "command"])
        
        assert success is False

    @patch("subprocess.run")
    def test_run_command_timeout(self, mock_run):
        """Test command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 10)
        
        handler = ADBHandler(use_root=False)
        success, output = handler._run_command(["test", "command"])
        
        assert success is False
        assert output == ""
