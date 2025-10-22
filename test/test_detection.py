#!/usr/bin/env python3
"""Test script to verify Instagram detection fix."""

import sys
sys.path.insert(0, '/home/han/MyWorkspace/TimerApps-CLI')

from src.adb_handler import ADBHandler
from src.config_manager import ConfigManager

def test_adb_connection():
    """Test if ADB is available."""
    print("Testing ADB connection...")
    adb = ADBHandler(use_root=False)
    if not adb.is_available:
        print("❌ ADB not available")
        return False
    print("✓ ADB connection OK")
    return True

def test_get_active_app():
    """Test getting active app."""
    print("\nTesting get_active_app()...")
    adb = ADBHandler(use_root=False)
    
    active_app = adb.get_active_app()
    if active_app:
        print(f"✓ Active app detected: {active_app}")
        return True
    else:
        print("⚠ No active app detected (this might be normal if no app is running)")
        return None

def test_with_instagram():
    """Test Instagram detection."""
    print("\nInstructions for testing Instagram detection:")
    print("1. Run this script")
    print("2. Open Instagram on your Android device")
    print("3. The script will check if Instagram is detected")
    print("\nWaiting for active app...")
    
    import time
    adb = ADBHandler(use_root=False)
    
    for i in range(6):  # Check for 30 seconds
        active_app = adb.get_active_app()
        print(f"[{i*5}s] Active app: {active_app}")
        
        if active_app and 'instagram' in active_app.lower():
            print(f"\n✓✓✓ SUCCESS! Instagram detected: {active_app}")
            return True
        
        if i < 5:
            time.sleep(5)
    
    print("\n⚠ Instagram not detected in 30 seconds")
    return False

if __name__ == "__main__":
    print("TimerApps-CLI - Detection Test\n")
    print("=" * 50)
    
    if not test_adb_connection():
        print("\nFix ADB connection first!")
        sys.exit(1)
    
    result = test_get_active_app()
    
    print("\n" + "=" * 50)
    print("\nStarting Instagram detection test...")
    test_with_instagram()
    
    print("\nTest complete!")
