#!/usr/bin/env python3
"""Debug ADB notification command generation and execution."""

import sys
sys.path.insert(0, '.')

from src.notifications import NotificationManager
import subprocess
from pathlib import Path


def show_adb_command_simulation():
    """Show what ADB command would be executed."""
    
    print("=" * 70)
    print("ADB Notification Command Simulation")
    print("=" * 70)
    
    nm = NotificationManager()
    
    print(f"\n📱 Device Status:")
    print(f"  - Use ADB: {nm.use_adb}")
    print(f"  - ADB Device: {nm.adb_device}")
    print(f"  - Enabled: {nm.enabled}")
    
    if not nm.use_adb:
        print("\n⚠️  Not using ADB fallback (termux-notification available directly)")
        return
    
    # Show command that would be executed
    print(f"\n📝 Example Commands That Will Be Executed:")
    print("-" * 70)
    
    examples = [
        ("Limit Reached", "Instagram", 60),
        ("Warning", "TikTok", 5),
        ("Custom", "TimerApps Test", None),
    ]
    
    for notify_type, app_name, param in examples:
        if notify_type == "Limit Reached":
            cmd = f'adb -s {nm.adb_device} shell termux-notification --title \'TimerApps - Limit Reached\' --content \'{app_name} limit ({param}m) exceeded. App is now blocked.\' --id 100'
        elif notify_type == "Warning":
            cmd = f'adb -s {nm.adb_device} shell termux-notification --title \'TimerApps - Warning\' --content \'{app_name}: Only {param}m remaining!\' --id 101'
        else:
            cmd = f'adb -s {nm.adb_device} shell termux-notification --title \'TimerApps Test\' --content \'This is a test notification from TimerApps-CLI via ADB\''
        
        print(f"\n{notify_type}:")
        print(f"  {cmd}")
    
    print("\n" + "=" * 70)
    print("Command Breakdown:")
    print("=" * 70)
    print("""
adb -s <device>              # Use specific ADB device
shell                         # Execute command on device shell
termux-notification           # Termux API command
  --title '<text>'           # Notification title
  --content '<text>'         # Notification content
  --id <number>              # Notification ID for tracking
""")


def show_adb_device_info():
    """Show available ADB devices."""
    
    print("\n" + "=" * 70)
    print("Available ADB Devices")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=3
        )
        
        print("\nADB Devices List:")
        print(result.stdout)
        
        # Parse devices
        lines = result.stdout.strip().split('\n')
        device_count = 0
        for line in lines:
            if line.strip() and "List of devices" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]
                    device_count += 1
                    
                    if status == "device":
                        print(f"✅ Device {device_count}: {device_id} (connected)")
                    elif status == "unauthorized":
                        print(f"❌ Device {device_count}: {device_id} (unauthorized - tap Allow on device)")
                    else:
                        print(f"⚠️  Device {device_count}: {device_id} ({status})")
        
        if device_count == 0:
            print("❌ No devices found!")
    
    except Exception as e:
        print(f"Error: {e}")


def show_notification_logic_flow():
    """Show the notification flow."""
    
    print("\n" + "=" * 70)
    print("Notification Flow Diagram")
    print("=" * 70)
    
    print("""
┌─────────────────────────────────────┐
│  Call: nm.send_limit_reached()      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Check: Is notification enabled?    │
│         - enabled = True ✓          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│  Check: use_adb flag?               │
│  - use_adb = True (direct not found)│
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Call: _send_notification_via_adb()                         │
│                                                             │
│  Build command:                                             │
│  adb -s localhost:5555 shell \\                             │
│    termux-notification \\                                   │
│      --title 'TimerApps - Limit Reached' \\                │
│      --content 'Instagram limit (60m) exceeded...' \\       │
│      --id 100                                               │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│  Execute command via subprocess.run()                       │
│  - Send to device via ADB                                   │
│  - Device executes in its shell                             │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
     ┌───────┴───────┐
     │               │
     ▼               ▼
 SUCCESS          FAILED
 (return=0)      (return!=0)
    │               │
    ✅             ❌
Log "sent"      Log error
    │               │
    └───────┬───────┘
            │
            ▼
      Return bool result
      
Note: If termux-notification is not available on device,
      you'll see: "/system/bin/sh: termux-notification: not found"
      This is EXPECTED on non-Termux devices!
""")


def show_when_it_works():
    """Show when notification via ADB will work."""
    
    print("\n" + "=" * 70)
    print("When Will Notifications via ADB Work?")
    print("=" * 70)
    
    print("""
✅ AKAN BERHASIL JIKA:
   1. Device terkoneksi via ADB
   2. Device adalah Termux (punya termux-notification command)
   3. Device authorized (no "unauthorized" status)
   4. Termux API package installed di Termux

❌ AKAN GAGAL JIKA:
   1. Device adalah standard Android (bukan Termux)
   2. Termux tidak punya termux-notification package
   3. Device unauthorized
   4. ADB connection error

📱 TESTING DI TERMUX:
   - Buka Termux langsung (bukan chroot)
   - Jalankan: timer daemon start
   - Notifications akan terkirim ke Android notification bar
   - Lihat di: ~/.timerapps/daemon.log

🐳 TESTING DI CHROOTANDROID:
   - Termux command tidak tersedia di chroot
   - ADB fallback automatically digunakan
   - Notifications dikirim via ADB ke device utama
   - Lihat di: ~/.timerapps/daemon.log
   - Device utama harus punya Termux + termux-api package
""")


if __name__ == "__main__":
    try:
        show_adb_command_simulation()
        show_adb_device_info()
        show_notification_logic_flow()
        show_when_it_works()
        
        print("\n" + "=" * 70)
        print("✅ Debug information displayed")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
