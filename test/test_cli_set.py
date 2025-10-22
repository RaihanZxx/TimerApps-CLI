#!/usr/bin/env python3
"""Test CLI set command with debugging."""

import sys
import time
sys.path.insert(0, '/home/han/MyWorkspace/TimerApps-CLI')

print("Test 1: Import modules")
start = time.time()

from src.config_manager import ConfigManager
print(f"  ✓ ConfigManager imported ({time.time()-start:.2f}s)")

from src.adb_handler import ADBHandler
print(f"  ✓ ADBHandler imported ({time.time()-start:.2f}s)")

from src.cli.click_cli import set as set_cmd
print(f"  ✓ CLI imported ({time.time()-start:.2f}s)")

print("\nTest 2: Initialize ConfigManager")
start = time.time()
config = ConfigManager()
print(f"  ✓ ConfigManager initialized ({time.time()-start:.2f}s)")

print("\nTest 3: Add app via ConfigManager directly")
start = time.time()
result = config.add_app("com.instagram.barcelona", "Barcelona", 60, "kill")
print(f"  ✓ App added: {result} ({time.time()-start:.2f}s)")

print("\nTest 4: Initialize ADBHandler")
start = time.time()
adb = ADBHandler(use_root=False)
print(f"  ✓ ADBHandler initialized ({time.time()-start:.2f}s)")
print(f"    - device_id: {adb.device_id}")
print(f"    - is_available: {adb.is_available}")

print("\nAll tests completed!")
