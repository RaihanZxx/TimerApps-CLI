# TimerApps-CLI 🚀

**Limit app usage on Termux to reduce distractions and increase productivity.**

A command-line timer application for Termux that automatically blocks or freezes Android apps when usage limit is reached. Built for Termux with support for both rooted and non-rooted devices.

## Features ✨

- **Smart Timer Pause/Resume**: Timer only counts when app is actively displayed
- **Dual Mode Support**: Root + ADB with automatic fallback
- **Auto-Kill/Freeze**: Automatically disable apps at limit
- **Daily Auto-Reset**: Timers reset automatically each day
- **Termux API Notifications**: Get notified when limits reached
- **Two UI Modes**:
  - Interactive: Modern Textual dashboard UI
  - Non-Interactive: Click CLI for scripting/automation
- **Battery Efficient**: Only monitors selected target apps
- **Persistent Database**: Track daily usage statistics

## Installation

### Requirements
- Termux environment
- Python 3.11+
- Either: Rooted device OR ADB connection

### Setup

```bash
cd TimerApps-CLI
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### First Run

```bash
timer
```

The app will auto-detect if your device is rooted and configure accordingly. If not rooted, ensure ADB is connected:

```bash
adb connect localhost:5555
```

## Usage

### Interactive Mode (Dashboard UI)

```bash
timer
```

Launch the interactive dashboard with:
- Real-time app usage tracking
- Quick stats overview
- Keyboard navigation

**Keyboard Shortcuts:**
- `L` - List all installed apps on device (with quick add option)
- `S` - Set/edit timer for existing app
- `A` - Add new app (manual entry)
- `R` - Reset all timers
- `Q` - Quit

### Non-Interactive Mode (CLI Commands)

#### Set timer for an app
```bash
timer set com.instagram.android 60
timer set com.tiktok.android 30 --action freeze
```

#### View all monitored apps
```bash
timer list
timer list -v  # Verbose with usage stats
```

#### Check usage status
```bash
timer status                           # Show all apps status
timer status com.instagram.android     # Show specific app
```

#### Reset timers
```bash
timer reset com.instagram.android      # Reset specific app
timer reset                             # Reset all apps
```

#### Freeze/unfreeze apps
```bash
timer freeze com.instagram.android         # Freeze app
timer freeze com.instagram.android -u      # Unfreeze app
```

#### View device info
```bash
timer info
```

#### Remove app from monitoring
```bash
timer remove
```

## Configuration

### Config Location
- **Config**: `~/.timerapps/config.json`
- **Database**: `~/.timerapps/db.json`
- **Logs**: `~/.timerapps/logs.log`

### Config Structure

```json
{
  "device": {
    "is_rooted": false,
    "use_adb": true
  },
  "apps": {
    "com.instagram.android": {
      "name": "Instagram",
      "limit_minutes": 60,
      "enabled": true,
      "action": "kill"
    }
  },
  "settings": {
    "check_interval": 5,
    "auto_reset_hour": 0,
    "notifications_enabled": true
  }
}
```

### Options

| Option | Value | Description |
|--------|-------|-------------|
| `check_interval` | seconds | How often to check active app (default: 5s) |
| `auto_reset_hour` | 0-23 | Hour for daily reset (default: 0 = midnight) |
| `notifications_enabled` | true/false | Show Termux API notifications |
| `action` | kill/freeze | What to do when limit reached |

## How It Works

### Timer Logic (Smart Pause/Resume)

```
User launches Instagram
  ↓
Timer starts counting (MONITORING)
  ↓
User closes app / switches to other app
  ↓
Timer PAUSES (but time remembered!)
  ↓
User returns to Instagram
  ↓
Timer RESUMES from where it paused
  ↓
Time used: 45m of 60m limit
  ↓
User switches away again
  ↓
Time remains: 45m (stays same until opened)
```

### App Enforcement

When app limit is reached:

1. **Kill** mode (default): `am force-stop com.package`
   - App closes immediately
   - Data may not save
   - User can reopen after reset

2. **Freeze** mode: `pm disable-user com.package`
   - App becomes unavailable
   - Cleaner than kill
   - User can unfreeze manually: `timer freeze com.package -u`

### Daily Reset

- Timers automatically reset at configured hour (default: 00:00)
- Previous day's statistics are archived
- Reset can be triggered manually: `timer reset`

## Workflow Example

### Day 1 Setup

```bash
# Add Instagram with 60 min limit
$ timer set com.instagram.android 60

# Add TikTok with 30 min limit  
$ timer set com.tiktok.android 30

# View configuration
$ timer list
📱 Monitored Apps:
✓ Instagram - 60m limit - Action: kill
✓ TikTok - 30m limit - Action: kill
```

### Day 1 Usage

```
09:00 - User opens Instagram
09:05 - Timer: 5m used (Timer MONITORING)
09:15 - User closes Instagram, opens YouTube
        Timer: 10m used (Timer PAUSED)
09:30 - User opens Instagram again
09:40 - Timer: 20m used (Timer RESUMED & MONITORING)
10:00 - User closes Instagram
        Timer: 40m used (Timer PAUSED)
10:30 - User opens Instagram again
        Timer: 40m used (Timer MONITORING)
11:30 - Timer: 60m used
        → Notification: "Instagram limit reached!"
        → App is blocked (killed/frozen)
12:00 - User tries to open Instagram - blocked!
```

### Day 2 (After Reset)

```
00:00 - Daily reset triggered
        Instagram timer: 0m / 60m ✓ Reset
        
09:00 - Fresh day, timer ready again
```

## Root vs ADB Mode

### Root Mode (`su`)
- ✅ Better control and stability
- ✅ No ADB connection needed
- ✅ More reliable command execution

### ADB Mode (Fallback)
- ✅ Works on non-rooted devices
- ✅ No need for superuser permissions
- ⚠️ Requires ADB connection
- ⚠️ Some commands may fail on certain Android versions

**Auto-Detection**: First run will detect your device and configure automatically.

## Notifications (Termux API)

Requires `termux-notification` command available. Notifications include:

- **Limit Reached**: When app usage exceeds configured limit
- **Daily Reset**: When timers reset each day
- **Warning**: When app has < 10% time remaining
- **Monitoring Started/Stopped**: When monitor service changes

To disable notifications:
```bash
# Edit ~/.timerapps/config.json
"notifications_enabled": false
```

## Database & Statistics

### Tracking

All usage is automatically logged to `~/.timerapps/db.json`:

```json
{
  "2024-10-22": {
    "com.instagram.android": {
      "name": "Instagram",
      "total_minutes_used": 45,
      "limit_minutes": 60,
      "remaining_minutes": 15,
      "sessions": [
        {"start": "09:15", "end": "09:25", "duration": 10},
        {"start": "10:30", "end": "10:50", "duration": 20}
      ],
      "limit_reached": false,
      "blocked_at": null
    }
  }
}
```

### View Statistics

```bash
# Check current day usage
$ timer status

# View specific app history
$ timer status com.instagram.android
```

## Troubleshooting

### Issue: "Device not rooted - using ADB fallback"

**Cause**: Device is not rooted, ADB will be used.

**Solution**: 
- Ensure ADB is installed: `apt install android-tools`
- Connect device: `adb connect localhost:5555`
- Or root your device for better stability

### Issue: "App won't freeze/kill"

**Cause**: 
- ADB not connected
- App is system app
- Missing permissions

**Solution**:
- Check ADB connection: `adb devices`
- Switch to kill mode: `timer set com.app 60 -a kill`
- Check logs: `cat ~/.timerapps/logs.log`

### Issue: Timer keeps resetting

**Cause**: Daily reset triggered

**Solution**:
- Normal behavior at configured reset hour (default: 00:00)
- Change reset hour in config file if desired

### Issue: No notifications appearing

**Cause**: 
- Termux API not available
- Notifications disabled in config

**Solution**:
- Check if termux-notification works: `termux-notification --title "Test" --content "Test"`
- Enable in config: `"notifications_enabled": true`

## Advanced Usage

### Scripting / Automation

```bash
#!/bin/bash

# Add multiple apps
timer set com.instagram.android 30
timer set com.tiktok.android 20
timer set com.facebook.android 45
timer set com.youtube.android 60

# Check all usage
timer status

# Reset at specific time (cron)
0 0 * * * timer reset
```

### Monitor in Background

The monitor runs when you use the interactive mode. To run continuously:

```bash
# Create a service script
cat > ~/.timerapps/monitor.sh << 'EOF'
#!/bin/bash
while true; do
  timer set com.instagram.android 60
  sleep 60
done
EOF

chmod +x ~/.timerapps/monitor.sh

# Run in background
~/.timerapps/monitor.sh &
```

### Custom Scripts

```python
# Python example
from src.config_manager import ConfigManager
from src.adb_handler import ADBHandler
from src.app_monitor import AppMonitor

config = ConfigManager()
adb = ADBHandler(use_root=config.get_device_rooted())
monitor = AppMonitor(config, adb)

# Get active app
active = adb.get_active_app()
print(f"Active: {active}")

# Get apps
apps = config.get_all_apps()
for pkg, data in apps.items():
    used = config.get_total_usage(pkg)
    print(f"{data['name']}: {used}m/{data['limit_minutes']}m")
```

## Project Structure

```
TimerApps-CLI/
├── pyproject.toml              # Project configuration
├── WORKFLOW_DESIGN.md          # Detailed architecture
├── README.md                   # This file
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point + router
│   ├── utils.py                # Utility functions
│   ├── config_manager.py       # Config/DB management
│   ├── adb_handler.py          # ADB/Root operations
│   ├── app_monitor.py          # Smart monitoring logic
│   ├── notifications.py        # Termux API
│   │
│   ├── cli/                    # Click CLI
│   │   ├── __init__.py
│   │   └── click_cli.py
│   │
│   └── ui/                     # Textual UI
│       ├── __init__.py
│       └── textual_dashboard.py
│
├── venv/                       # Virtual environment
│
└── ~/.timerapps/               # User data (auto-created)
    ├── config.json             # App config
    ├── db.json                 # Usage database
    └── logs.log                # Activity logs
```

## API Documentation

### ConfigManager

```python
config = ConfigManager()

# Apps management
config.add_app(package, name, limit_minutes, action="kill")
config.update_app_limit(package, limit_minutes)
config.get_app(package)
config.get_all_apps()
config.remove_app(package)
config.enable_app(package, enabled=True)

# Usage tracking
config.update_app_usage(package, used_minutes)
config.get_total_usage(package)
config.get_remaining_time(package)
config.mark_limit_reached(package)

# Resetting
config.reset_app_timer(package)
config.reset_all_timers()
config.check_and_reset_daily()
```

### ADBHandler

```python
adb = ADBHandler(use_root=False)

# App info
adb.get_active_app()
adb.get_installed_apps()
adb.is_app_running(package)

# App control
adb.kill_app(package)
adb.freeze_app(package)
adb.unfreeze_app(package)

# Detection
adb.detect_root()
```

### AppMonitor

```python
monitor = AppMonitor(config_mgr, adb_handler, notify_mgr)

# Control
monitor.start()
monitor.stop()
monitor.is_running()

# App state
monitor.get_app_state(package)  # Returns TimerState
monitor.get_app_used_time(package)
monitor.get_app_used_minutes(package)

# Reset
monitor.reset_app(package)
monitor.reset_all()
```

## Performance & Battery

### Resource Usage
- **CPU**: ~0.5% per monitored app (checking every 5s)
- **Memory**: ~50-100MB for the app
- **Battery**: Minimal impact, efficient thread sleeping

### Optimization
- Only monitors apps you explicitly add
- Pauses timer when app not active
- Efficient database writes (batched)
- Thread-based background monitoring

## Security & Privacy

- All data stored locally in `~/.timerapps/`
- No cloud sync or external connections
- ADB/Root only used for app control
- Logs contain activity timestamps only
- Can manually review/delete logs anytime

## Contributing

Pull requests welcome! Areas for contribution:
- UI improvements
- Better ADB command handling
- Cross-platform support
- Test coverage
- Documentation

## License

MIT License - See LICENSE file for details

## Author

Made by RaihanZxx for Termux productivity

---

**Questions or Issues?** Check the Troubleshooting section or open an issue on GitHub.

Happy productivity! 🎯
