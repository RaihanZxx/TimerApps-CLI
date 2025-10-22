# Daemon Mode & Background Monitoring

## Overview

TimerApps-CLI sekarang mendukung **background daemon mode** yang sempurna untuk environment chroot seperti setup Anda (ChrootAndroid di `/data/local/tmp/chrootubuntu/`).

Daemon mode memastikan monitoring tetap berjalan bahkan ketika:
- Terminal Termux ditutup
- Shell script parent (`start.sh`) dihentikan
- Process awal yang memanggil monitoring sudah exit

## How It Works

### Foreground Mode (Existing)
```bash
timer start
```
- Runs monitoring in current shell process
- **AKAN BERHENTI** ketika shell ditutup atau parent exit
- Berguna untuk testing/debugging

### Background Daemon Mode (NEW)
```bash
timer daemon start
```
- **Properly daemonizes** menggunakan double-fork technique
- **TETAP BERJALAN** bahkan ketika parent shell ditutup
- Logs semua activities ke `~/.timerapps/daemon.log`
- Tracks PID di `~/.timerapps/daemon.pid`

## Commands

### Start Daemon
```bash
timer daemon start
```
Output:
```
🚀 Starting daemon...
📱 Monitoring 2 app(s)
✓ Daemon started successfully
  PID: 12345
  Log: /home/han/.timerapps/daemon.log

View logs with: tail -f ~/.timerapps/daemon.log
Stop daemon with: timer daemon stop
```

### Check Status
```bash
timer daemon status
```
Output:
```
📊 Daemon Status:
──────────────────────────────────────────────
Status: ✓ RUNNING
PID: 12345
Log File: /home/han/.timerapps/daemon.log
PID File: /home/han/.timerapps/daemon.pid

📝 Recent Logs (last 10 lines):
──────────────────────────────────────────────
  [2025-10-22 23:15:00] [INFO] Daemon started with PID 12345
  [2025-10-22 23:15:01] [INFO] Monitor started
  [2025-10-22 23:15:01] [INFO] Start monitoring: com.instagram.android
  ...
```

### View Logs
```bash
# Show last 50 lines
timer daemon logs

# Follow logs (like tail -f)
timer daemon logs -f

# Show custom number of lines
timer daemon logs -n 100
```

### Stop Daemon
```bash
timer daemon stop
```

### Restart Daemon
```bash
timer daemon restart
```

## Setup untuk ChrootAndroid

Anda bisa mengintegrasikan daemon mode dengan `start.sh` Anda:

### Option 1: Start daemon dan exit (Recommended)
```bash
#!/bin/bash
# /data/local/tmp/start.sh

# Enter chroot
cd /data/local/tmp/chrootubuntu/

# Install/setup if needed
if [ ! -d "home/user/.timerapps" ]; then
    # Initial setup...
fi

# Start daemon dan exit - daemon akan tetap jalan
su -c 'sh -c "cd /data/local/tmp/chrootubuntu && chroot . /bin/bash -c \"timer daemon start\"" &'

# Atau dengan nohup jika perlu extra safety
su -c 'sh -c "nohup timer daemon start > /dev/null 2>&1 &"'

echo "Daemon started in background"
```

### Option 2: Start daemon dan monitor (Testing)
```bash
#!/bin/bash
# /data/local/tmp/start.sh

su -c 'sh -c "cd /data/local/tmp/chrootubuntu && chroot . /bin/bash -c \"timer daemon start\"'
```

### Option 3: Start daemon dengan auto-restart di boot (Advanced)
Jika environment Anda punya init system:
```bash
# Buat init script
mkdir -p /data/local/tmp/chrootubuntu/etc/init.d/
cat > /data/local/tmp/chrootubuntu/etc/init.d/timerapps << 'EOF'
#!/bin/bash
### BEGIN INIT INFO
# Provides: timerapps
# Required-Start: $local_fs
# Required-Stop: $local_fs
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
### END INIT INFO

case "$1" in
  start)
    timer daemon start
    ;;
  stop)
    timer daemon stop
    ;;
  restart)
    timer daemon restart
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
    ;;
esac
EOF

chmod +x /data/local/tmp/chrootubuntu/etc/init.d/timerapps
```

## Technical Details

### Daemonization Process

1. **First Fork**: Creates child process, parent exits
   - Detaches from terminal session

2. **Decouple from Environment**:
   - Changes to root directory
   - Creates new session with `setsid()`
   - Sets umask

3. **Second Fork**: Prevents daemon from reacquiring terminal
   - Final parent exits
   - Child continues as daemon

4. **Redirect I/O**:
   - stdin: `/dev/null`
   - stdout/stderr: `~/.timerapps/daemon.log`

### PID Tracking

```
~/.timerapps/daemon.pid
├─ Contains daemon PID
├─ Checked on startup to prevent duplicate daemons
└─ Removed on graceful shutdown
```

### Signal Handling

- `SIGTERM`: Graceful shutdown, saves state
- `SIGINT`: Same as SIGTERM
- Daemon handles cleanup automatically

## Integration dengan ADB Fallback

Daemon mode bekerja seamlessly dengan ADB fallback untuk notifications:

```
Daemon Start
    ↓
NotificationManager Init
    ├─ Check termux-notification available?
    │   ├─ YES → Use direct termux-notification
    │   └─ NO → Setup ADB fallback
    └─ Enable ADB device detection
    
App Limit Reached
    ↓
Send Notification
    ├─ Use ADB method if termux-notification unavailable
    └─ Log to daemon.log
```

## Troubleshooting

### Daemon tidak jalan?
```bash
# Check status
timer daemon status

# View logs
timer daemon logs -f

# Manually restart
timer daemon restart
```

### Process tetap berjalan setelah stop?
```bash
# Force kill daemon
kill $(cat ~/.timerapps/daemon.pid)

# Or safer way
pkill -f "timer daemon start"
```

### Logs tidak terlihat?
```bash
# Check log file exists
ls -la ~/.timerapps/daemon.log

# Check content
tail -f ~/.timerapps/daemon.log

# Make sure daemon is running
timer daemon status
```

## Performance

- **Memory**: ~50-100 MB (Python + monitoring threads)
- **CPU**: ~5-10% when idle (periodic app checking)
- **Disk**: ~1-2 MB logs per day (depending on activity)

## Next Steps

1. **Setup daemon start in your chroot startup script**:
   ```bash
   timer daemon start
   ```

2. **Monitor status**:
   ```bash
   timer daemon status
   timer daemon logs -f
   ```

3. **Configure apps**:
   ```bash
   timer set com.instagram.android 60
   timer set com.tiktok.android 30
   ```

4. **Verify it's running**:
   - Close Termux window
   - Wait 5 minutes
   - Open Termux again
   - Check: `timer daemon status` → Should show RUNNING ✓
