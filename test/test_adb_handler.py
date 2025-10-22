#!/usr/bin/env python3
"""Test ADB Handler without actual device."""

import sys
sys.path.insert(0, '/home/han/MyWorkspace/TimerApps-CLI')

from src.adb_handler import ADBHandler
import unittest
from unittest.mock import patch, MagicMock

class TestADBHandler(unittest.TestCase):
    """Test ADB handler methods."""
    
    def test_adb_shell_method_exists(self):
        """Test that _adb_shell method exists."""
        adb = ADBHandler(use_root=False)
        self.assertTrue(hasattr(adb, '_adb_shell'))
        self.assertTrue(callable(getattr(adb, '_adb_shell')))
    
    def test_get_active_app_parsing(self):
        """Test get_active_app parsing with mock."""
        with patch('subprocess.run') as mock_run:
            # Mock successful ADB response
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  mCurrentFocus=Window{abc123u0 com.instagram.android/com.instagram.MainActivity}"
            )
            
            adb = ADBHandler(use_root=False)
            result = adb.get_active_app()
            
            # Should extract instagram package
            self.assertEqual(result, "com.instagram.android")
            print("✓ get_active_app parsing works correctly")
    
    def test_get_active_app_no_output(self):
        """Test get_active_app with no output."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=""
            )
            
            adb = ADBHandler(use_root=False)
            result = adb.get_active_app()
            
            self.assertIsNone(result)
            print("✓ get_active_app handles empty output")
    
    def test_methods_accept_correct_parameters(self):
        """Test that methods accept correct parameters."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test"
            )
            
            adb = ADBHandler(use_root=False)
            
            # These should not raise exceptions
            adb.get_installed_apps()
            adb.kill_app("com.test.app")
            adb.freeze_app("com.test.app")
            adb.unfreeze_app("com.test.app")
            adb.is_app_running("com.test.app")
            
            print("✓ All methods accept correct parameters")

if __name__ == '__main__':
    print("Testing ADB Handler Methods\n")
    print("=" * 60)
    
    unittest.main(verbosity=2)
