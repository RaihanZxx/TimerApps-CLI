#!/usr/bin/env python3
"""Test notification system with ADB fallback capability."""

import sys
sys.path.insert(0, '.')

from src.notifications import NotificationManager
from src.utils import log_message


def test_notification_initialization():
    """Test that NotificationManager initializes correctly."""
    nm = NotificationManager()
    
    print(f"✓ NotificationManager initialized")
    print(f"  - enabled: {nm.enabled}")
    print(f"  - use_adb: {nm.use_adb}")
    print(f"  - adb_device: {nm.adb_device}")
    
    assert nm.enabled, "NotificationManager should be enabled"
    if nm.use_adb:
        assert nm.adb_device, "ADB device should be detected if use_adb is True"
        print(f"✓ ADB fallback enabled with device: {nm.adb_device}")
    else:
        print(f"✓ Using direct termux-notification")
    

def test_notification_methods():
    """Test that all notification methods exist and can be called."""
    nm = NotificationManager()
    
    test_app = "com.example.app"
    test_limit = 30
    
    methods_to_test = [
        ("send_limit_reached", lambda: nm.send_limit_reached(test_app, test_limit)),
        ("send_warning", lambda: nm.send_warning(test_app, 5)),
        ("send_limit_reset", lambda: nm.send_limit_reset(test_app)),
        ("send_app_unfrozen", lambda: nm.send_app_unfrozen(test_app)),
        ("send_monitoring_started", lambda: nm.send_monitoring_started(1)),
        ("send_monitoring_stopped", lambda: nm.send_monitoring_stopped()),
        ("send_custom", lambda: nm.send_custom("Test", "Test content")),
    ]
    
    for method_name, method_call in methods_to_test:
        try:
            result = method_call()
            print(f"✓ {method_name}: callable and executed")
        except Exception as e:
            print(f"✗ {method_name}: {e}")
            raise


def test_notification_clearing():
    """Test notification clearing functionality."""
    nm = NotificationManager()
    
    try:
        result = nm.clear_notification(100)
        print(f"✓ clear_notification: callable")
        
        result = nm.clear_all()
        print(f"✓ clear_all: callable")
    except Exception as e:
        print(f"✗ Clearing failed: {e}")
        raise


def test_fallback_detection():
    """Test that fallback detection works."""
    nm = NotificationManager()
    
    if nm.use_adb:
        print(f"✓ ADB fallback detected (termux-notification not available)")
        print(f"  - ADB send via: adb -s {nm.adb_device} shell termux-notification ...")
    else:
        print(f"✓ Direct termux-notification available")
        print(f"  - Send via: termux-notification ...")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing NotificationManager with ADB Fallback")
    print("=" * 60)
    
    try:
        test_notification_initialization()
        print()
        
        test_fallback_detection()
        print()
        
        test_notification_methods()
        print()
        
        test_notification_clearing()
        print()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
