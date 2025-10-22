#!/usr/bin/env python3
"""Test sending actual notification via ADB."""

import sys
sys.path.insert(0, '.')

from src.notifications import NotificationManager
from src.utils import log_message
import time


def test_send_notification_via_adb():
    """Test sending various notifications via ADB."""
    
    print("=" * 60)
    print("Testing ADB Notification Send")
    print("=" * 60)
    
    # Initialize notification manager
    nm = NotificationManager()
    
    print(f"\n✓ NotificationManager initialized")
    print(f"  - Enabled: {nm.enabled}")
    print(f"  - Use ADB: {nm.use_adb}")
    print(f"  - ADB Device: {nm.adb_device}")
    print()
    
    if not nm.enabled:
        print("✗ Notifications disabled!")
        sys.exit(1)
    
    if not nm.use_adb:
        print("⚠️  Using direct termux-notification (not ADB)")
    
    # Test 1: Limit Reached Notification
    print("-" * 60)
    print("Test 1: Send 'Limit Reached' Notification")
    print("-" * 60)
    result = nm.send_limit_reached("Instagram", 60)
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 2: Warning Notification
    print("\nTest 2: Send 'Warning' Notification")
    print("-" * 60)
    result = nm.send_warning("TikTok", 5)
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 3: Custom Notification
    print("\nTest 3: Send Custom Notification")
    print("-" * 60)
    result = nm.send_custom(
        "Timer Test",
        "This is a test notification from TimerApps-CLI via ADB"
    )
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 4: Daily Reset
    print("\nTest 4: Send 'Daily Reset' Notification")
    print("-" * 60)
    result = nm.send_limit_reset("Facebook")
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 5: App Unfrozen
    print("\nTest 5: Send 'App Unfrozen' Notification")
    print("-" * 60)
    result = nm.send_app_unfrozen("WhatsApp")
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 6: Monitoring Started
    print("\nTest 6: Send 'Monitoring Started' Notification")
    print("-" * 60)
    result = nm.send_monitoring_started(5)
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    # Test 7: Monitoring Stopped
    print("\nTest 7: Send 'Monitoring Stopped' Notification")
    print("-" * 60)
    result = nm.send_monitoring_stopped()
    print(f"Result: {'✓ SUCCESS' if result else '✗ FAILED'}")
    time.sleep(1)
    
    print("\n" + "=" * 60)
    print("✓ All notifications sent!")
    print("=" * 60)
    
    # Show logs
    print("\n📝 Logs from system:")
    print("-" * 60)
    import subprocess
    result = subprocess.run(
        ["tail", "-20", str(Path.home() / ".timerapps" / "logs.log")],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        for line in result.stdout.split('\n')[-15:]:
            if line.strip():
                print(line)
    print()


if __name__ == "__main__":
    from pathlib import Path
    
    try:
        test_send_notification_via_adb()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
