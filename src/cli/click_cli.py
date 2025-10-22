import click
import sys
import time
import os
import signal
from typing import Optional

from ..config_manager import ConfigManager
from ..adb_handler import ADBHandler
from ..app_monitor import AppMonitor
from ..notifications import NotificationManager
from ..utils import format_time, get_progress_bar, log_message


config_mgr: Optional[ConfigManager] = None
adb: Optional[ADBHandler] = None
notify: Optional[NotificationManager] = None
monitor: Optional[AppMonitor] = None


def init_managers(skip_monitor: bool = False) -> None:
    """Initialize all managers. skip_monitor=True for faster CLI commands."""
    global config_mgr, adb, notify, monitor
    
    config_mgr = ConfigManager()
    
    # Quick ADB initialization (with timeout)
    use_root = config_mgr.get_device_rooted() or False
    adb = ADBHandler(use_root=use_root)
    
    # Disable notifications for CLI to avoid hang
    notify = NotificationManager(enabled=False)
    
    # Only init monitor if needed (skipped for faster CLI)
    if not skip_monitor:
        # Enable notifications for interactive mode
        notify.enabled = config_mgr.config["settings"]["notifications_enabled"]
        monitor = AppMonitor(config_mgr, adb, notify)


@click.group()
def cli():
    """TimerApps-CLI: App usage timer for Termux."""
    pass


@cli.command()
@click.argument("package")
@click.argument("limit_minutes", type=int)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-a", "--action", type=click.Choice(["kill", "freeze"]), 
              default="kill", help="Action when limit reached")
@click.option("-n", "--name", default=None, help="Custom app name (auto-detect if not provided)")
def set(package: str, limit_minutes: int, verbose: bool, action: str, name: str) -> None:
    """Set time limit for an app.
    
    Example: timer set com.instagram.android 60
    """
    init_managers(skip_monitor=True)
    
    if not config_mgr or not adb:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    if limit_minutes <= 0:
        click.secho("Error: Limit must be positive", fg="red")
        sys.exit(1)
    
    # Get app name: custom > from device > fallback to package name
    if name:
        app_name = name
    else:
        click.secho("Fetching app name from device...", fg="cyan")
        app_name = adb.get_app_name(package)
    
    # Add or update app
    if package in config_mgr.get_all_apps():
        config_mgr.update_app_limit(package, limit_minutes)
        config_mgr.update_app_name(package, app_name)
        msg = f"Updated: {app_name} → {limit_minutes}m"
    else:
        config_mgr.add_app(package, app_name, limit_minutes, action)
        msg = f"Added: {app_name} ({package}) with {limit_minutes}m limit"
    
    click.secho(msg, fg="green")
    
    if verbose:
        click.echo(f"  Package: {package}")
        click.echo(f"  App Name: {app_name}")
        click.echo(f"  Action: {action}")
        click.echo(f"  Limit: {limit_minutes} minutes")


@cli.command("list")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def list_apps(verbose: bool) -> None:
    """List all monitored apps."""
    init_managers(skip_monitor=True)
    
    if not config_mgr:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    apps = config_mgr.get_all_apps()
    
    if not apps:
        click.secho("No apps configured yet.", fg="yellow")
        return
    
    click.secho("\n📱 Monitored Apps:", bold=True, fg="cyan")
    click.echo("─" * 70)
    
    for package, app_data in apps.items():
        status = "✓ Enabled" if app_data["enabled"] else "✗ Disabled"
        click.secho(f"\n{app_data['name']}", bold=True)
        click.echo(f"  Package: {package}")
        click.echo(f"  Limit: {app_data['limit_minutes']} minutes")
        click.echo(f"  Action: {app_data['action']}")
        click.secho(f"  Status: {status}", fg="green" if app_data["enabled"] else "red")
        
        if verbose:
            used = config_mgr.get_total_usage(package)
            remaining = config_mgr.get_remaining_time(package)
            bar = get_progress_bar(used, app_data['limit_minutes'])
            click.echo(f"  Usage: {used}m / {app_data['limit_minutes']}m [{bar}]")
            click.echo(f"  Remaining: {remaining}m")


@cli.command()
@click.argument("package", required=False)
def status(package: Optional[str]) -> None:
    """Show usage status. If no package, show all."""
    init_managers(skip_monitor=True)
    
    if not config_mgr:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    if package:
        # Show specific app
        app_data = config_mgr.get_app(package)
        if not app_data:
            click.secho(f"App not found: {package}", fg="red")
            sys.exit(1)
        
        used = config_mgr.get_total_usage(package)
        remaining = config_mgr.get_remaining_time(package)
        limit = app_data["limit_minutes"]
        bar = get_progress_bar(used, limit)
        
        click.secho(f"\n{app_data['name']}", bold=True, fg="cyan")
        click.echo(f"  Usage:    {used}m / {limit}m [{bar}]")
        click.echo(f"  Remaining: {remaining}m ({int(remaining/limit*100)}%)")
        
        if config_mgr.is_limit_reached_today(package):
            click.secho("  Status: 🔒 BLOCKED", fg="red")
        else:
            pct = int(used / limit * 100)
            if pct >= 90:
                click.secho(f"  Status: ⚠️  WARNING ({pct}%)", fg="yellow")
            else:
                click.secho(f"  Status: ✓ OK ({pct}%)", fg="green")
    else:
        # Show all apps
        click.secho("\n📊 Usage Status:", bold=True, fg="cyan")
        click.echo("─" * 70)
        
        apps = config_mgr.get_all_apps()
        if not apps:
            click.secho("No apps configured.", fg="yellow")
            return
        
        for pkg, app_data in apps.items():
            used = config_mgr.get_total_usage(pkg)
            remaining = config_mgr.get_remaining_time(pkg)
            limit = app_data["limit_minutes"]
            bar = get_progress_bar(used, limit, width=15)
            pct = int(used / limit * 100) if limit > 0 else 0
            
            status_icon = "✓"
            status_color = "green"
            
            if config_mgr.is_limit_reached_today(pkg):
                status_icon = "🔒"
                status_color = "red"
            elif pct >= 90:
                status_icon = "⚠️"
                status_color = "yellow"
            
            click.echo(f"{status_icon} {app_data['name']:<25} {used:>3}m/{limit:<3}m [{bar}]")


@cli.command()
@click.argument("package", required=False)
def reset(package: Optional[str]) -> None:
    """Reset timer for app(s). If no package, reset all."""
    init_managers(skip_monitor=True)
    
    if not config_mgr:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    if package:
        # Reset specific app
        if config_mgr.reset_app_timer(package):
            click.secho(f"✓ Reset timer for {package}", fg="green")
        else:
            click.secho(f"Error: App not found or already reset", fg="red")
            sys.exit(1)
    else:
        # Reset all
        count = config_mgr.reset_all_timers()
        click.secho(f"✓ Reset all timers ({count} apps)", fg="green")


@cli.command()
@click.argument("package")
@click.option("-u", "--unfreeze", is_flag=True, help="Unfreeze instead of freeze")
def freeze(package: str, unfreeze: bool) -> None:
    """Freeze or unfreeze an app."""
    init_managers(skip_monitor=True)
    
    if not adb:
        click.secho("Error: ADB handler not initialized", fg="red")
        sys.exit(1)
    
    if unfreeze:
        if adb.unfreeze_app(package):
            click.secho(f"✓ Unfroze: {package}", fg="green")
        else:
            click.secho(f"Error: Failed to unfreeze {package}", fg="red")
            sys.exit(1)
    else:
        if adb.freeze_app(package):
            click.secho(f"✓ Froze: {package}", fg="green")
        else:
            click.secho(f"Error: Failed to freeze {package}", fg="red")
            sys.exit(1)


@cli.command()
def remove() -> None:
    """Remove an app from monitoring."""
    init_managers(skip_monitor=True)
    
    if not config_mgr:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    apps = config_mgr.get_all_apps()
    if not apps:
        click.secho("No apps configured.", fg="yellow")
        return
    
    click.secho("Choose app to remove:", fg="cyan")
    app_list = list(apps.items())
    for i, (pkg, data) in enumerate(app_list, 1):
        click.echo(f"{i}. {data['name']} ({pkg})")
    
    try:
        choice = click.prompt("Select (number)", type=int)
        if 1 <= choice <= len(app_list):
            pkg, data = app_list[choice - 1]
            config_mgr.remove_app(pkg)
            click.secho(f"✓ Removed: {data['name']}", fg="green")
        else:
            click.secho("Invalid choice", fg="red")
    except (ValueError, click.Abort):
        click.secho("Cancelled", fg="yellow")


@cli.command()
def info() -> None:
    """Show device and configuration info."""
    init_managers()
    
    if not config_mgr or not adb:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    is_rooted = config_mgr.get_device_rooted()
    
    click.secho("\n📱 Device Info:", bold=True, fg="cyan")
    click.echo(f"  Rooted: {'Yes' if is_rooted else 'No'}")
    click.echo(f"  ADB Available: {adb.is_available}")
    
    click.secho("\n⚙️  Settings:", bold=True, fg="cyan")
    settings = config_mgr.config["settings"]
    click.echo(f"  Check Interval: {settings['check_interval']}s")
    click.echo(f"  Auto Reset Hour: {settings['auto_reset_hour']}:00")
    click.echo(f"  Notifications: {'Enabled' if settings['notifications_enabled'] else 'Disabled'}")
    
    click.secho("\n📊 Monitored Apps:", bold=True, fg="cyan")
    apps = config_mgr.get_all_apps()
    click.echo(f"  Total: {len(apps)}")
    
    if apps:
        total_limit = sum(app["limit_minutes"] for app in apps.values())
        click.echo(f"  Total Limit: {total_limit}m")


@cli.command("adb-auth")
def adb_auth() -> None:
    """Authorize ADB device connection.
    
    Run this if you see 'unauthorized' errors.
    """
    click.secho("\n🔐 ADB Device Authorization Guide\n", fg="cyan", bold=True)
    
    click.echo("Follow these steps:")
    click.echo("1. Connect your Android device via USB")
    click.echo("2. Enable USB Debugging on your device:")
    click.echo("   - Go to Settings → Developer Options → USB Debugging")
    click.echo("   - Tap Allow (or OK) when prompted")
    click.echo("3. Check connection:")
    click.echo()
    
    import subprocess
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        click.secho("Current ADB devices:", fg="yellow")
        click.echo(result.stdout)
        
        if "unauthorized" in result.stdout:
            click.secho("⚠️  Device is unauthorized!", fg="red")
            click.echo("\nYou should see a dialog on your Android device.")
            click.echo("Tap 'Allow' to authorize this connection.")
            click.echo()
            click.echo("Then run: adb devices")
            click.echo("Device should show as 'device' (not 'unauthorized')")
        elif "device" in result.stdout and "offline" not in result.stdout:
            click.secho("✓ Device is authorized and ready!", fg="green")
        else:
            click.secho("⚠️  No devices found", fg="yellow")
            click.echo("Make sure:")
            click.echo("- USB cable is connected properly")
            click.echo("- USB Debugging is enabled")
            click.echo("- Device is not locked")
    except Exception as e:
        click.secho(f"Error: {e}", fg="red")


@cli.command()
def start() -> None:
    """Start monitoring apps in background.
    
    This will continuously monitor and block apps based on set limits.
    Press Ctrl+C to stop.
    """
    init_managers(skip_monitor=False)
    
    if not config_mgr or not monitor:
        click.secho("Error: Failed to initialize", fg="red")
        sys.exit(1)
    
    apps = config_mgr.get_all_apps()
    if not apps:
        click.secho("Error: No apps configured. Add apps first with:", fg="red")
        click.echo("  timer set com.app.name 60")
        sys.exit(1)
    
    click.secho("\n🚀 Starting monitoring...", fg="green", bold=True)
    click.echo(f"📱 Monitoring {len(apps)} app(s)")
    click.echo("Press Ctrl+C to stop\n")
    
    # Enable notifications
    if notify:
        notify.enabled = config_mgr.config["settings"]["notifications_enabled"]
    
    try:
        monitor.start()
        
        # Keep the process running
        while True:
            time.sleep(1)
            
            # Optional: Print status every 60 seconds
            if int(time.time()) % 60 == 0:
                limited_apps = []
                for pkg, app_data in apps.items():
                    if config_mgr.is_limit_reached_today(pkg):
                        limited_apps.append(app_data["name"])
                
                if limited_apps:
                    click.secho(f"⚠️  Blocked apps: {', '.join(limited_apps)}", fg="yellow")
    
    except KeyboardInterrupt:
        click.secho("\n\n⏹️  Stopping monitor...", fg="yellow")
        monitor.stop()
        click.secho("✓ Monitor stopped", fg="green")
    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg="red")
        if monitor and monitor.is_running():
            monitor.stop()
        sys.exit(1)


def get_cli():
    """Get Click CLI group."""
    return cli
