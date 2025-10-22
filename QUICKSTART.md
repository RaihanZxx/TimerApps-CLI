# TimerApps-CLI - Quick Start Guide 🚀

## Installation (5 minutes)

```bash
# Clone/navigate to project
cd TimerApps-CLI

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install package
pip install -e .
```

## First Run

```bash
# Launch app
timer
```

✅ First time setup will auto-detect your device (rooted or ADB)

## Basic Examples

### Add Apps to Monitor

```bash
# Instagram with 60 min limit
timer set com.instagram.android 60

# TikTok with 30 min limit, freeze instead of kill
timer set com.tiktok.android 30 --action freeze

# Facebook with 45 min limit
timer set com.facebook.android 45
```

### View Apps & Usage

```bash
# List all monitored apps
timer list

# Show detailed usage for all apps
timer list -v

# Check specific app status
timer status com.instagram.android

# Show all apps status with progress bars
timer status
```

### Control Timers

```bash
# Reset specific app timer
timer reset com.instagram.android

# Reset ALL timers (usually after midnight)
timer reset

# Manually freeze/unfreeze app
timer freeze com.instagram.android           # Freeze
timer freeze com.instagram.android -u        # Unfreeze

# Remove app from monitoring
timer remove
```

## How It Works

### Smart Timer Logic

```
User opens Instagram
  ↓
Timer STARTS counting (only while app is open)
  ↓
User closes app / switches to another app
  ↓
Timer PAUSES (remembers time already used)
  ↓
User opens Instagram again
  ↓
Timer RESUMES (continues from paused time, not reset!)
  ↓
When time limit reached
  ↓
App is BLOCKED (killed or frozen)
```

### Example Scenario

```
Instagram limit: 60 minutes

09:00 - Open Instagram (0m used, timer starts)
09:30 - Close Instagram (30m used, timer pauses)
10:00 - Open TikTok for 15 minutes
10:15 - Close TikTok
10:15 - Open Instagram again (timer resumes at 30m)
11:15 - Close Instagram (60m used total)
        → "Limit reached! Instagram blocked" ⚠️
11:30 - Try to open Instagram - BLOCKED! 🔒
00:00 - Next day - timer resets, Instagram available again
```

## Two Modes

### Mode 1: Interactive Dashboard

```bash
timer
```

Opens a real-time dashboard with:
- App usage progress bars
- Quick stats overview
- Keyboard shortcuts

Press `L` for list, `S` to set timer, `R` to reset, `Q` to quit

### Mode 2: Non-Interactive CLI

```bash
timer set com.app 60
timer status
timer reset
```

Perfect for scripts and automation.

## Configuration Files

Automatically created in `~/.timerapps/`:

```
~/.timerapps/
├── config.json     # App limits and settings
├── db.json         # Daily usage database
└── logs.log        # Activity logs
```

### Customize Settings

Edit `~/.timerapps/config.json`:

```json
{
  "settings": {
    "check_interval": 5,              // Check every 5 seconds
    "auto_reset_hour": 0,             // Reset at 00:00 (midnight)
    "notifications_enabled": true      // Show Termux notifications
  }
}
```

## Troubleshooting

### "Device not rooted - using ADB fallback"

This is normal. The app auto-detected your device type.

For non-rooted devices, ensure ADB is connected:
```bash
adb connect localhost:5555
```

### "Termux notification not available"

Notifications will still work in logs, but won't show popups. To fix:
```bash
apt install termux-api
```

### App won't freeze/kill

Try kill mode instead of freeze:
```bash
timer set com.app 60 --action kill
```

### Need to unblock app before reset time?

```bash
timer freeze com.instagram.android -u  # Unfreeze
timer set com.instagram.android 60     # Re-enable monitoring
timer reset com.instagram.android      # Reset timer
```

## Important Features

✨ **Smart Pause/Resume** - Timer only counts when app is actively displayed

✨ **Battery Efficient** - Only checks target apps you add

✨ **Persistent** - All data saved to local database

✨ **Daily Reset** - Automatically resets each day at 00:00

✨ **Dual Control** - Works with Root OR ADB (auto-detected)

✨ **Notifications** - Get alerted when limits reached

✨ **Two UIs** - Interactive dashboard or CLI commands

## Next Steps

1. Read **WORKFLOW_DESIGN.md** for architecture details
2. Check **README.md** for complete documentation
3. Run `timer info` to see your device configuration
4. Add your first app: `timer set com.app.name 60`
5. Use `timer status` to monitor usage

## Keyboard Shortcuts (Interactive Mode)

| Key | Action |
|-----|--------|
| L | List monitored apps |
| S | Set/edit timer |
| A | Add new app |
| R | Reset all timers |
| Q | Quit application |

## Example: Full Workflow

```bash
# 1. Setup
timer                               # First run - auto setup

# 2. Add apps to limit
timer set com.instagram.android 60
timer set com.tiktok.android 30
timer set com.youtube.android 120

# 3. Check configuration
timer list -v

# 4. Monitor usage (runs in background once set up)
timer status

# 5. When limit reached
# → App will be blocked automatically
# → You'll get a notification
# → App can be unfrozen if needed

# 6. Next day (or manual reset)
timer reset
```

## File Locations

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point + router |
| `src/utils.py` | Utility functions |
| `src/config_manager.py` | Config & database |
| `src/adb_handler.py` | ADB/Root operations |
| `src/app_monitor.py` | Core monitoring logic |
| `src/notifications.py` | Termux API |
| `src/cli/click_cli.py` | CLI commands |
| `src/ui/textual_dashboard.py` | Interactive UI |

---

**Ready to boost your productivity?** 🎯

```bash
timer set com.instagram.android 60
timer set com.tiktok.android 30
timer status
```

Enjoy distraction-free time! ✨
