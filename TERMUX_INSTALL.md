# TimerApps-CLI Installation for Termux 📱

Complete installation guide for Termux environment on Android.

## Prerequisites

### 1. Termux Installation
- Download from F-Droid or Google Play
- Grant file/storage permissions
- Update packages: `apt update && apt upgrade`

### 2. Python 3.11+
```bash
apt install python3 python3-pip
python3 --version  # Verify 3.11+
```

### 3. Git (for cloning repo)
```bash
apt install git
```

### 4. ADB or Root Access

**Option A: Non-rooted + ADB**
```bash
apt install android-tools
adb connect localhost:5555
```

**Option B: Rooted Device**
- Install Magisk or similar
- Grant Termux superuser access

## Installation Steps

### Step 1: Clone Repository

```bash
cd ~
git clone https://github.com/RaihanZxx/TimerApps-CLI.git
cd TimerApps-CLI
```

Or if you have the folder already:
```bash
cd /path/to/TimerApps-CLI
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This will install:
- `textual` - Interactive UI
- `click` - CLI framework

### Step 4: Verify Installation

```bash
timer --version
# Output: TimerApps-CLI, version 0.0.1

timer --help
# Shows all available commands
```

## First Time Setup

### Run First Time
```bash
timer
```

The app will:
1. Auto-detect if device is rooted
2. Create `~/.timerapps/` directory
3. Generate config files
4. Show welcome screen

### Allow Permissions

When prompted:
- ✅ Grant Termux notification permissions
- ✅ If rooted: Grant superuser access
- ✅ If not rooted: Ensure ADB is connected

## Termux-Specific Setup

### 1. Enable Notification API (Optional)

For notifications to work:
```bash
apt install termux-api
```

Then grant permissions:
- Open Termux Settings
- Enable "Allow external apps"

### 2. Setup ADB Connection (If Not Rooted)

In Termux:
```bash
adb connect localhost:5555
```

On your computer (if using adb from there):
```bash
# On your machine
adb connect <your-device-ip>:5555
```

### 3. Auto-start Monitoring (Optional)

Create a startup script:
```bash
cat > ~/.timerapps/start_monitor.sh << 'EOF'
#!/bin/bash
cd ~/TimerApps-CLI
source venv/bin/activate
timer
EOF

chmod +x ~/.timerapps/start_monitor.sh
```

Then add to Termux startup or use a task scheduler.

## Troubleshooting (Termux-Specific)

### Issue: "Command 'python3' not found"

**Solution:**
```bash
apt install python3
```

### Issue: "Permission denied" on startup

**Solution:**
```bash
chmod +x ~/TimerApps-CLI/src/main.py
```

### Issue: "No module named 'textual'"

**Solution:**
```bash
source ~/TimerApps-CLI/venv/bin/activate
pip install textual click
```

### Issue: ADB not connecting

**Solution:**
```bash
# Enable Developer Mode on Android device
# Enable USB Debugging in Settings > Developer Options

# Connect via localhost
adb connect localhost:5555

# Or connect via IP
adb connect <device-ip>:5555

# Verify connection
adb devices
```

### Issue: "Device not rooted" but I have root

**Solution:**
Make sure Termux has superuser permissions:
1. Open Termux
2. Type: `su`
3. If prompted, grant root access
4. Verify: `whoami` should return "root"

### Issue: Notifications not showing

**Solution:**
```bash
# Install termux-api
apt install termux-api

# Test notification
termux-notification --title "Test" --content "Test"
```

## Daily Usage in Termux

### Opening Terminal (Multiple Sessions)

Termux allows multiple terminal sessions. Recommended setup:

- **Session 1**: Run timer interactive mode
  ```bash
  cd ~/TimerApps-CLI
  source venv/bin/activate
  timer
  ```

- **Session 2**: Use for other commands
  ```bash
  cd ~/TimerApps-CLI
  source venv/bin/activate
  timer list
  timer status
  ```

### Shortcut to Timer Commands

Create an alias in `~/.bashrc`:
```bash
echo 'alias timer="~/TimerApps-CLI/venv/bin/timer"' >> ~/.bashrc
source ~/.bashrc

# Now you can just type:
timer set com.app 60
timer status
```

### Create Desktop Shortcut (Termux Desktop)

If using Termux:GUI or similar:
```bash
cat > ~/.local/share/applications/timer.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=TimerApps
Exec=bash -c 'cd ~/TimerApps-CLI && source venv/bin/activate && timer'
Icon=alarm
Terminal=true
EOF
```

## File Structure in Termux

```
~/ (home directory)
├── TimerApps-CLI/
│   ├── src/
│   ├── venv/
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── TERMUX_INSTALL.md
│   └── WORKFLOW_DESIGN.md
│
└── .timerapps/                (auto-created)
    ├── config.json
    ├── db.json
    └── logs.log
```

## Persistence Across Reboots

To auto-start monitoring on boot, you can use Tasker or create a background service.

### Option 1: Cron Job (if crond available)

```bash
apt install cronie
crond -b  # Start crond daemon

# Add to crontab
crontab -e

# Add line:
@reboot /home/user/TimerApps-CLI/venv/bin/python -m timer
```

### Option 2: Termux Boot

Install and use Termux:Boot app:
```bash
# Create boot script
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_timer << 'EOF'
#!/bin/bash
cd ~/TimerApps-CLI
source venv/bin/activate
nohup timer > ~/.timerapps/monitor.log 2>&1 &
EOF

chmod +x ~/.termux/boot/start_timer
```

## Performance Tips

### 1. Reduce Check Interval (Save Battery)

Edit `~/.timerapps/config.json`:
```json
{
  "settings": {
    "check_interval": 10  // Check every 10 sec instead of 5
  }
}
```

### 2. Monitor Only Essential Apps

Only add apps you really need to limit - each app costs ~0.5% CPU.

### 3. Use Freeze Instead of Kill

Kill mode forces app to stop. Freeze is lighter:
```bash
timer set com.app 60 --action freeze
```

### 4. Disable Notifications if Battery Low

```bash
# Edit ~/.timerapps/config.json
"notifications_enabled": false
```

## Update & Maintenance

### Update Package

```bash
cd ~/TimerApps-CLI
git pull origin main
pip install -e . --upgrade
```

### Check Logs

```bash
cat ~/.timerapps/logs.log
tail -f ~/.timerapps/logs.log  # Follow logs in real-time
```

### Clear Old Data

```bash
# Archive old stats
cp ~/.timerapps/db.json ~/.timerapps/db.json.backup

# Reset database
echo '{}' > ~/.timerapps/db.json
```

## Useful Termux Commands

```bash
# Check battery status
termux-battery-status

# Check device info
termux-device-info

# Storage location
echo $PREFIX

# Share a file
termux-share /path/to/file

# Vibrate/notify
termux-vibrate 500

# Get clipboard
termux-clipboard-get

# Set clipboard
echo "text" | termux-clipboard-set
```

## Advanced: Running as a Service

Create a more robust monitoring daemon:

```bash
cat > ~/.timerapps/daemon.sh << 'EOF'
#!/bin/bash

LOG_FILE="$HOME/.timerapps/daemon.log"

while true; do
    {
        echo "[$(date)] Starting TimerApps monitor..."
        cd $HOME/TimerApps-CLI
        source venv/bin/activate
        python -m src.main
    } >> "$LOG_FILE" 2>&1
    
    echo "[$(date)] Monitor crashed, restarting in 10s..." >> "$LOG_FILE"
    sleep 10
done
EOF

chmod +x ~/.timerapps/daemon.sh

# Run in background
nohup ~/.timerapps/daemon.sh > ~/.timerapps/daemon.log 2>&1 &
```

Then kill with:
```bash
pkill -f daemon.sh
```

## Getting Help

### Check Documentation
- `README.md` - Full documentation
- `QUICKSTART.md` - Quick examples
- `WORKFLOW_DESIGN.md` - Technical details

### View Logs
```bash
cat ~/.timerapps/logs.log
```

### Check Configuration
```bash
cat ~/.timerapps/config.json | python3 -m json.tool
```

### Reset Configuration
```bash
rm ~/.timerapps/config.json
# On next run, it will regenerate
```

## Next Steps

1. Complete installation steps above
2. Run `timer --version` to verify
3. Read `QUICKSTART.md` for usage examples
4. Add your first app: `timer set com.instagram.android 60`
5. Check status: `timer status`

---

**Happy productivity limiting!** 🎯

For issues or questions, check the logs or refer to `README.md`.
