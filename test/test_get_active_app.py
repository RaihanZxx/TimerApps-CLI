#!/usr/bin/env python3
"""Test get_active_app() with debug logging."""

import sys
sys.path.insert(0, '/home/han/MyWorkspace/TimerApps-CLI')

from src.adb_handler import ADBHandler
from src.utils import log_message

print("Testing get_active_app()...\n")

adb = ADBHandler(use_root=False)

print(f"ADB Available: {adb.is_available}")
print(f"Use Root: {adb.use_root}\n")

print("Calling get_active_app()...\n")
active_app = adb.get_active_app()

print(f"\nResult: {active_app}\n")

# Show logs
print("\n" + "="*60)
print("Logs from ~/.timerapps/logs.log:")
print("="*60)

import os
log_file = os.path.expanduser("~/.timerapps/logs.log")
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        content = f.read()
        if content:
            print(content)
        else:
            print("(empty)")
else:
    print("(file not found)")
