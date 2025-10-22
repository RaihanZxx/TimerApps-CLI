#!/usr/bin/env python3
"""Test CLI set command directly."""

import sys
import time
sys.path.insert(0, '/home/han/MyWorkspace/TimerApps-CLI')

print("Importing Click...")
import click
print("✓ Click imported")

print("\nImporting CLI...")
from src.cli.click_cli import cli
print("✓ CLI imported")

print("\nTesting set command with CliRunner...")
from click.testing import CliRunner

runner = CliRunner()

print("Test 1: timer set com.test.app1 60")
start = time.time()
result = runner.invoke(cli, ["set", "com.test.app1", "60"])
elapsed = time.time() - start
print(f"  Exit code: {result.exit_code}")
print(f"  Time: {elapsed:.2f}s")
print(f"  Output: {result.output}")
if result.exception:
    print(f"  Exception: {result.exception}")

print("\nTest 2: timer list")
start = time.time()
result = runner.invoke(cli, ["list"])
elapsed = time.time() - start
print(f"  Exit code: {result.exit_code}")
print(f"  Time: {elapsed:.2f}s")
print(f"  Output (first 200 chars): {result.output[:200]}")

print("\nDone!")
