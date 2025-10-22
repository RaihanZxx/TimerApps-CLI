# TimerApps-CLI - Complete Workflow Design

## 1. ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────┐
│                   TimerApps-CLI                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─── main.py (Router) ──────────────────────────────┐  │
│  │  ├─ Interactive Mode (--interactive / no args)   │  │
│  │  └─ Non-Interactive Mode (--timer app_package)   │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│  ┌────────────────┴─────────────────────────────────┐  │
│  │         UI Layer / Click CLI                     │  │
│  ├─────────────────────────────────────────────────┤  │
│  │ Textual (Interactive)   │   Click (Non-int)     │  │
│  │ ├─ Dashboard           │   ├─ timer set        │  │
│  │ ├─ App List            │   ├─ timer start      │  │
│  │ ├─ Set Timer           │   ├─ timer stop       │  │
│  │ ├─ Monitor Real-time   │   ├─ timer list       │  │
│  │ └─ Statistics          │   └─ timer reset      │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│  ┌────────────────┴─────────────────────────────────┐  │
│  │         Core Logic Layer                        │  │
│  ├─────────────────────────────────────────────────┤  │
│  │  config_manager.py    │   app_monitor.py        │  │
│  │  ├─ Load/Save JSON    │   ├─ Get active app    │  │
│  │  ├─ Timer tracking    │   ├─ Calculate used    │  │
│  │  ├─ Daily reset       │   ├─ Smart pause/resume│  │
│  │  └─ Stats generation  │   └─ Enforce limits    │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│  ┌────────────────┴─────────────────────────────────┐  │
│  │         System Integration Layer                │  │
│  ├─────────────────────────────────────────────────┤  │
│  │  adb_handler.py       │ notifications.py        │  │
│  │  ├─ Root check        │ ├─ Termux API          │  │
│  │  ├─ ADB fallback      │ ├─ Notifications       │  │
│  │  ├─ Get app list      │ └─ Logging             │  │
│  │  ├─ Kill/Freeze app   │                        │  │
│  │  └─ Get active app    │                        │  │
│  └────────────────────────────────────────────────┘  │
│                   ↓                                    │
│  ┌────────────────────────────────────────────────┐  │
│  │         Storage Layer                          │  │
│  ├────────────────────────────────────────────────┤  │
│  │  ~/.timerapps/config.json  (Main config)       │  │
│  │  ~/.timerapps/db.json      (Usage database)    │  │
│  │  ~/.timerapps/logs.log     (Activity logs)     │  │
│  └────────────────────────────────────────────────┘  │
│                   ↓                                    │
│  ┌────────────────────────────────────────────────┐  │
│  │         Device Layer (ADB / Root)              │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## 2. DATA STRUCTURES

### Config File (~/.timerapps/config.json)
```json
{
  "device": {
    "is_rooted": true,
    "use_adb": false
  },
  "apps": {
    "com.instagram.android": {
      "name": "Instagram",
      "limit_minutes": 60,
      "enabled": true,
      "action": "kill"  // "kill" or "freeze"
    },
    "com.tiktok.android": {
      "name": "TikTok",
      "limit_minutes": 30,
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

### Database File (~/.timerapps/db.json)
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
        {"start": "10:30", "end": "10:50", "duration": 20},
        {"start": "14:00", "end": "14:15", "duration": 15}
      ],
      "limit_reached": false,
      "blocked_at": null
    }
  }
}
```

## 3. WORKFLOW STATES

### Timer State Machine
```
         ┌─────────────────────┐
         │     INACTIVE        │  (App not running)
         └────────┬────────────┘
                  │ App launched by user
                  ↓
         ┌─────────────────────┐
         │    MONITORING       │  (Timer running, counting down)
         └────────┬────────────┘
                  │ Time elapsed OR
                  │ User manually stops app
                  ↓
         ┌─────────────────────┐
         │    PAUSED           │  (App running, but timer paused)
         └────────┬────────────┘
                  │ User resumes app
                  ↓
         ┌─────────────────────┐
         │    MONITORING       │  (Back to monitoring)
         └────────┬────────────┘
                  │ Limit reached
                  ↓
         ┌─────────────────────┐
         │    BLOCKED          │  (App killed/frozen)
         └────────┬────────────┘
                  │ Daily reset (00:00)
                  ↓
         ┌─────────────────────┐
         │    INACTIVE         │
         └─────────────────────┘
```

## 4. MONITORING LOGIC

```python
ACTIVE_APP = get_active_app()

# Check if timer should be running
if ACTIVE_APP in MONITORED_APPS:
    if TIMER_STATE == "PAUSED" and was_running:
        TIMER_STATE = "MONITORING"  # Resume counting
    elif TIMER_STATE == "INACTIVE":
        TIMER_STATE = "MONITORING"  # Start counting
else:
    if TIMER_STATE == "MONITORING":
        TIMER_STATE = "PAUSED"  # Pause counting, but remember
    ACTIVE_APP = None

# Check time limit
if TIMER_STATE == "MONITORING":
    USED_TIME += CHECK_INTERVAL
    if USED_TIME >= LIMIT:
        kill_or_freeze_app()
        send_notification()
        TIMER_STATE = "BLOCKED"
```

## 5. EXECUTION MODES

### Mode 1: Interactive (Textual UI)
```bash
$ timer
# Opens dashboard with real-time monitoring

Dashboard:
┌─────────────────────────────────────────────┐
│  🚀 TimerApps-CLI Dashboard                │
├─────────────────────────────────────────────┤
│                                             │
│ Quick Stats:                                │
│  Instagram: 45m / 60m [████████░░] 75%    │
│  TikTok:    10m / 30m [███░░░░░░░] 33%    │
│                                             │
│ Monitored Apps (2):                         │
│  ✓ com.instagram.android  60 min  [ACTIVE] │
│  ✓ com.tiktok.android     30 min  [PAUSED] │
│                                             │
│ [+] Add App | [✎] Edit | [►] Manage       │
│                                             │
└─────────────────────────────────────────────┘

Keyboard Shortcuts:
  L - List all apps
  S - Set timer
  A - Add monitored app
  R - Reset timers
  Q - Quit
```

### Mode 2: Non-Interactive (Click CLI)
```bash
# Add/set timer
$ timer set com.instagram.android 60

# Start monitoring in background
$ timer start

# View active timers
$ timer list

# View current stats
$ timer status com.instagram.android

# Stop monitoring
$ timer stop

# Reset all timers
$ timer reset

# Verbose output
$ timer set com.instagram.android 60 -v
```

## 6. FEATURE BREAKDOWN

### F1: Dual Detection (Root / ADB)
- ✅ Check if device is rooted
- ✅ If rooted: Use `su` commands for kill/freeze
- ✅ If not rooted: Fallback to ADB commands
- ✅ Autodetect or user choice on first run

### F2: Smart Timer Pause/Resume
- ✅ Monitor active app every 5 seconds
- ✅ Only count time when app is ACTIVELY displayed
- ✅ If user switches to another app: Timer PAUSES
- ✅ If user returns to app: Timer RESUMES (not reset)
- ✅ Used time carried over from previous session

### F3: App Kill/Freeze
- ✅ Kill: `pm force-stop com.app.package` (loses state)
- ✅ Freeze: `pm disable-user com.app.package` (can re-enable)
- ✅ Send notification before action
- ✅ Log action to database

### F4: Daily Auto-Reset
- ✅ Reset happens at 00:00 (configurable)
- ✅ Only resets ENABLED monitored apps
- ✅ Preserves yesterday's stats in database
- ✅ Timer task runs every second to check reset time

### F5: Termux API Notifications
- ✅ Show notification: `termux-notification --title "Warning" --content "Instagram limit reached"`
- ✅ Ring notification: `termux-notification-remove 100`
- ✅ Log all actions with timestamps

### F6: Target-Only Monitoring
- ✅ Get list of all installed apps
- ✅ User selects only apps to monitor
- ✅ Background daemon only checks monitored apps
- ✅ CPU/Battery: Only ~2% per app monitored

## 7. DATABASE RESET LOGIC

```python
def check_and_reset_daily():
    current_date = datetime.now().strftime("%Y-%m-%d")
    last_reset_date = config.get("last_reset_date")
    
    if current_date != last_reset_date:
        # Archive yesterday's data
        archive_old_data()
        
        # Reset all enabled apps
        for app_package, app_data in config["apps"].items():
            if app_data["enabled"]:
                reset_app_timer(app_package)
        
        # Update config
        config["last_reset_date"] = current_date
        save_config()
        
        notify("Daily timers reset!")
```

## 8. FILE STRUCTURE

```
TimerApps-CLI/
├── pyproject.toml
├── WORKFLOW_DESIGN.md        (This file)
├── src/
│   ├── __init__.py
│   ├── main.py               (Entry point + router)
│   ├── adb_handler.py        (ADB/Root operations)
│   ├── app_monitor.py        (Active app tracking)
│   ├── config_manager.py     (Config/DB management)
│   ├── notifications.py      (Termux API)
│   ├── utils.py              (Helper functions)
│   ├── cli/
│   │   ├── __init__.py
│   │   └── click_cli.py      (Non-interactive Click CLI)
│   └── ui/
│       ├── __init__.py
│       └── textual_dashboard.py  (Interactive Textual UI)
├── .timerapps/               (User data directory)
│   ├── config.json
│   ├── db.json
│   └── logs.log
└── tests/
    └── test_core.py
```

## 9. KEY IMPLEMENTATION DETAILS

### Smart Pause/Resume Algorithm
```
LAST_ACTIVE_APP = None
TIMER_STATE = "INACTIVE"

while True:
    CURRENT_ACTIVE = get_active_app()
    
    if CURRENT_ACTIVE in MONITORED_APPS:
        if CURRENT_ACTIVE != LAST_ACTIVE_APP:
            LAST_ACTIVE_APP = CURRENT_ACTIVE
            TIMER_STATE = "MONITORING"
            session_start = now()
        
        if TIMER_STATE == "MONITORING":
            used_time += INTERVAL
            if used_time >= limit:
                kill_app(CURRENT_ACTIVE)
                TIMER_STATE = "BLOCKED"
    else:
        if LAST_ACTIVE_APP in MONITORED_APPS:
            TIMER_STATE = "PAUSED"  # Pause but don't reset
    
    sleep(5)  # Check every 5 seconds
```

### Graceful Shutdown
- ✅ On SIGTERM/SIGINT: Save current state
- ✅ Close file handles properly
- ✅ Log shutdown event
- ✅ Notify user if app was in BLOCKED state

## 10. SETUP & REQUIREMENTS

### Python Dependencies
- `textual` - Interactive TUI framework
- `click` - CLI argument parsing
- `psutil` - System info (optional, for performance)
- `pydantic` - Config validation (optional)

### System Requirements
- Termux on Android 8+
- ADB OR Root access (or both for fallback)
- Python 3.11+

### First-Time Setup
1. Install: `pip install -e .` or `pip install .`
2. Run: `timer` (interactive mode will guide setup)
3. Allow Termux notifications
4. Set up ADB if not rooted: `adb connect localhost:5555`
