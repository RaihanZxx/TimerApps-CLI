#!/usr/bin/env python3
"""Test daemon manager functionality."""

import sys
import time
import os
sys.path.insert(0, '.')

from src.daemon_manager import DaemonManager
from pathlib import Path


def test_daemon_initialization():
    """Test DaemonManager initialization."""
    dm = DaemonManager()
    
    print("✓ DaemonManager initialized")
    print(f"  - PID file: {dm.pid_file}")
    print(f"  - Log file: {dm.daemon_log}")
    print(f"  - PID file parent exists: {dm.pid_file.parent.exists()}")
    
    assert dm.pid_file.parent.exists(), "PID file directory should exist"


def test_daemon_status():
    """Test daemon status checking."""
    dm = DaemonManager()
    status = dm.get_status()
    
    print("✓ Daemon status retrieved")
    print(f"  - Running: {status['running']}")
    print(f"  - PID: {status['pid']}")
    print(f"  - Log file: {status['log_file']}")
    
    assert isinstance(status['running'], bool), "Status should have running field"
    assert 'pid' in status, "Status should have pid field"


def test_pid_file_operations():
    """Test PID file read/write operations."""
    dm = DaemonManager()
    
    # Cleanup old pid file if exists
    if dm.pid_file.exists():
        dm.pid_file.unlink()
    
    test_pid = 12345
    dm._write_pid(test_pid)
    
    print("✓ PID file written")
    print(f"  - Test PID: {test_pid}")
    
    assert dm.pid_file.exists(), "PID file should exist after write"
    content = dm.pid_file.read_text().strip()
    assert int(content) == test_pid, "PID file should contain correct PID"
    
    # Cleanup
    dm.pid_file.unlink()
    print("✓ PID file cleaned up")


def test_process_exists_check():
    """Test process existence checking."""
    dm = DaemonManager()
    
    # Check current process (should exist)
    current_pid = os.getpid()
    exists = dm._process_exists(current_pid)
    
    print(f"✓ Process existence check")
    print(f"  - Current PID: {current_pid}")
    print(f"  - Exists: {exists}")
    
    assert exists, "Current process should exist"
    
    # Check non-existent process (should not exist)
    fake_pid = 999999999
    not_exists = not dm._process_exists(fake_pid)
    
    assert not_exists, "Non-existent process should return False"
    print(f"  - Fake PID check: OK (returns False as expected)")


def test_cleanup_handler():
    """Test cleanup handler."""
    dm = DaemonManager()
    
    # Write a test PID file
    test_pid = 54321
    dm._write_pid(test_pid)
    assert dm.pid_file.exists(), "PID file should exist"
    
    # Call cleanup
    dm._cleanup()
    
    print("✓ Cleanup handler executed")
    print(f"  - PID file removed: {not dm.pid_file.exists()}")
    
    assert not dm.pid_file.exists(), "PID file should be removed by cleanup"


def test_daemon_commands_help():
    """Test that daemon commands have proper help text."""
    from click.testing import CliRunner
    from src.cli.click_cli import daemon
    
    runner = CliRunner()
    
    # Test daemon group help
    result = runner.invoke(daemon, ['--help'])
    print("✓ Daemon group help text")
    print(f"  - Exit code: {result.exit_code}")
    print(f"  - Contains 'start': {'start' in result.output}")
    print(f"  - Contains 'stop': {'stop' in result.output}")
    print(f"  - Contains 'status': {'status' in result.output}")
    
    assert result.exit_code == 0, "Help command should succeed"
    assert 'start' in result.output.lower(), "Help should mention start"
    assert 'stop' in result.output.lower(), "Help should mention stop"
    assert 'status' in result.output.lower(), "Help should mention status"


def test_daemon_status_command():
    """Test daemon status CLI command."""
    from click.testing import CliRunner
    from src.cli.click_cli import daemon_status
    
    runner = CliRunner()
    result = runner.invoke(daemon_status)
    
    print("✓ Daemon status command executed")
    print(f"  - Exit code: {result.exit_code}")
    print(f"  - Output contains 'Status': {'Status' in result.output}")
    print(f"  - Output contains 'PID': {'PID' in result.output}")
    
    assert result.exit_code == 0, "Status command should succeed"
    assert 'Status' in result.output, "Output should show status"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Daemon Manager")
    print("=" * 60)
    
    try:
        test_daemon_initialization()
        print()
        
        test_daemon_status()
        print()
        
        test_pid_file_operations()
        print()
        
        test_process_exists_check()
        print()
        
        test_cleanup_handler()
        print()
        
        test_daemon_commands_help()
        print()
        
        test_daemon_status_command()
        print()
        
        print("=" * 60)
        print("✓ All daemon tests passed!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
