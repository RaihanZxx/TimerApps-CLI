#!/usr/bin/env python3
"""
TimerApps-CLI - App Usage Timer for Termux
Main entry point that routes to interactive or non-interactive mode
"""

import sys
import click
from typing import Optional

from .config_manager import ConfigManager
from .adb_handler import ADBHandler
from .app_monitor import AppMonitor
from .notifications import NotificationManager
from .cli.click_cli import get_cli
from .utils import log_message


def setup_first_time() -> None:
    """Setup for first-time run."""
    config_mgr = ConfigManager()
    
    if config_mgr.get_device_rooted() is None:
        click.secho("\n🔧 First-time setup detected!", fg="cyan", bold=True)
        click.echo("\nDetecting device capabilities...")
        
        # Create temporary ADB handler to detect root
        adb_temp = ADBHandler(use_root=False)
        is_rooted = adb_temp.detect_root()
        
        config_mgr.set_device_rooted(is_rooted)
        
        if is_rooted:
            click.secho("✓ Device is rooted - using su commands", fg="green")
        else:
            click.secho("⚠ Device not rooted - using ADB fallback", fg="yellow")
            click.echo("  Make sure ADB is connected!")
        
        click.secho("\n✓ Setup complete! Ready to use.", fg="green")


def show_help_banner() -> None:
    """Show help banner for interactive mode."""
    click.clear()
    click.secho("\n╔═══════════════════════════════════════╗", fg="cyan")
    click.secho("║     🚀 TimerApps-CLI v0.0.1           ║", fg="cyan", bold=True)
    click.secho("║  App Usage Timer for Termux           ║", fg="cyan")
    click.secho("╚═══════════════════════════════════════╝\n", fg="cyan")
    
    click.secho("Interactive Mode - Keyboard Shortcuts:", fg="yellow", bold=True)
    click.echo("  L - List apps")
    click.echo("  S - Set timer")
    click.echo("  A - Add app")
    click.echo("  R - Reset timers")
    click.echo("  Q - Quit")
    click.echo()
    
    click.secho("Non-Interactive Mode Examples:", fg="yellow", bold=True)
    click.echo("  timer set com.instagram.android 60    # Set 60 min limit")
    click.echo("  timer list                             # List all apps")
    click.echo("  timer status                           # Show usage")
    click.echo("  timer reset                            # Reset timers")
    click.echo()


def run_interactive() -> None:
    """Run in interactive mode with Textual dashboard."""
    try:
        from .ui.textual_dashboard import run_interactive as run_textual
    except ImportError:
        click.secho("Error: Textual not installed", fg="red")
        click.echo("Install with: pip install textual")
        sys.exit(1)
    
    config_mgr = ConfigManager()
    
    # Auto-detect root
    if config_mgr.get_device_rooted() is None:
        is_rooted = ADBHandler(use_root=False).detect_root()
        config_mgr.set_device_rooted(is_rooted)
    
    use_root = config_mgr.get_device_rooted()
    adb = ADBHandler(use_root=use_root)
    
    notify_enabled = config_mgr.config["settings"]["notifications_enabled"]
    notify = NotificationManager(enabled=notify_enabled)
    
    monitor = AppMonitor(config_mgr, adb, notify)
    
    try:
        run_textual(config_mgr, adb, monitor, notify)
    except KeyboardInterrupt:
        if monitor.is_running():
            monitor.stop()
        click.secho("\nMonitoring stopped.", fg="yellow")
    except Exception as e:
        log_message(f"Interactive mode error: {e}", "ERROR")
        click.secho(f"\nError: {e}", fg="red")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.version_option("0.0.1", prog_name="TimerApps-CLI")
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    TimerApps-CLI - App Usage Timer for Termux
    
    Limit app usage with automatic blocking when limit is reached.
    
    Usage:
      timer              # Interactive mode (Textual dashboard)
      timer [command]    # Non-interactive mode
    
    Examples:
      timer set com.instagram.android 60
      timer list
      timer status com.instagram.android
      timer reset
    """
    
    # Check if this is first run
    config_mgr = ConfigManager()
    if config_mgr.get_device_rooted() is None:
        setup_first_time()
    
    # If no subcommand, run interactive mode
    if ctx.invoked_subcommand is None:
        show_help_banner()
        run_interactive()


# Add CLI commands from click_cli module
cli_group = get_cli()
for cmd_name, cmd in cli_group.commands.items():
    if cmd_name not in main.commands:
        main.add_command(cmd, name=cmd_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.secho("\n\nInterrupted by user.", fg="yellow")
        sys.exit(0)
    except Exception as e:
        log_message(f"Fatal error: {e}", "ERROR")
        click.secho(f"\nFatal error: {e}", fg="red")
        sys.exit(1)
