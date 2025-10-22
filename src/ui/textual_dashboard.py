from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Button, DataTable, Header, Footer, Input, Label
from textual.screen import Screen
from textual import work
from textual.reactive import reactive

from ..config_manager import ConfigManager
from ..adb_handler import ADBHandler
from ..app_monitor import AppMonitor, TimerState
from ..notifications import NotificationManager
from ..utils import format_time, get_progress_bar


class DashboardScreen(Screen):
    """Main dashboard screen showing app timers."""
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("l", "list_apps", "List Apps"),
        ("s", "set_timer", "Set Timer"),
        ("a", "add_app", "Add App"),
        ("r", "reset_all", "Reset All"),
    ]
    
    def __init__(self, config_mgr: ConfigManager, adb: ADBHandler,
                 monitor: AppMonitor, notify: NotificationManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.adb = adb
        self.monitor = monitor
        self.notify = notify
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("🚀 TimerApps-CLI Dashboard", id="title")
            with Horizontal():
                yield Static("Quick Stats:", id="stats-label", classes="section-header")
            with Container(id="stats-container"):
                yield Static("Loading stats...", id="stats-content")
            
            with Horizontal():
                yield Static("Monitored Apps:", id="apps-label", classes="section-header")
            yield DataTable(id="apps-table")
            
            with Horizontal():
                yield Button("Add App", id="btn-add", variant="primary")
                yield Button("Edit", id="btn-edit", variant="default")
                yield Button("Manage", id="btn-manage", variant="default")
                yield Button("Quit", id="btn-quit", variant="error")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Setup dashboard on mount."""
        self._setup_apps_table()
        self._update_stats()
        self._update_display()
        self.periodic_update()
    
    def _setup_apps_table(self) -> None:
        """Setup the apps data table."""
        table = self.query_one("#apps-table", DataTable)
        table.add_columns("App", "Status", "Used/Limit", "Progress", "Action")
    
    def _update_stats(self) -> None:
        """Update quick stats section."""
        apps = self.config_mgr.get_all_apps()
        if not apps:
            stats_text = "No apps configured yet."
        else:
            stats_text = ""
            for package, app_data in apps.items():
                used = self.config_mgr.get_total_usage(package)
                limit = app_data["limit_minutes"]
                
                bar = get_progress_bar(used, limit, width=15)
                pct = int(used / limit * 100) if limit > 0 else 0
                
                status_icon = "✓"
                if self.config_mgr.is_limit_reached_today(package):
                    status_icon = "🔒"
                elif pct >= 90:
                    status_icon = "⚠️"
                
                line = f"{status_icon} {app_data['name']}: {used}m/{limit}m [{bar}] {pct}%\n"
                stats_text += line
            
            stats_text = stats_text.strip()
        
        # Update existing stats widget
        stats_widget = self.query_one("#stats-content", Static)
        stats_widget.update(stats_text)
    
    def _update_display(self) -> None:
        """Update the full dashboard display."""
        self._update_stats()
        self._update_apps_table()
    
    def _update_apps_table(self) -> None:
        """Update apps table with current data."""
        table = self.query_one("#apps-table", DataTable)
        table.clear()
        
        apps = self.config_mgr.get_all_apps()
        
        for package, app_data in apps.items():
            used = self.config_mgr.get_total_usage(package)
            limit = app_data["limit_minutes"]
            remaining = max(0, limit - used)
            
            bar = get_progress_bar(used, limit, width=10)
            
            status = "✓ Enabled" if app_data["enabled"] else "✗ Disabled"
            limit_reached = "🔒 Blocked" if self.config_mgr.is_limit_reached_today(package) else "Active"
            used_str = f"{used}/{limit}m"
            
            table.add_row(app_data["name"], status, used_str, bar, limit_reached)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn-quit":
            self.app.exit()
        elif button_id == "btn-add":
            self.action_add_app()
        elif button_id == "btn-edit":
            self.action_set_timer()
        elif button_id == "btn-manage":
            self.action_manage()
    
    def action_quit(self) -> None:
        """Quit the application."""
        if self.monitor.is_running():
            self.monitor.stop()
        self.app.exit()
    
    def action_list_apps(self) -> None:
        """Show list of installed apps on device."""
        self.app.push_screen(ListInstalledAppsScreen(self.adb, self.config_mgr, self.notify))
    
    def action_set_timer(self) -> None:
        """Set timer for an app."""
        self.app.push_screen(SetTimerScreen(self.config_mgr, self.notify, self._update_display))
    
    def action_add_app(self) -> None:
        """Add a new app to monitor."""
        self.app.push_screen(AddAppScreen(self.config_mgr, self.notify, self._update_display))
    
    def action_manage(self) -> None:
        """Manage apps."""
        self.app.push_screen(ManageAppsScreen(self.config_mgr, self.monitor, self.notify, self._update_display))
    
    def action_reset_all(self) -> None:
        """Reset all timers."""
        count = self.monitor.reset_all()
        self.notify.send_custom("TimerApps", f"Reset {count} app timers")
        self._update_display()
    
    @work(exclusive=True)
    async def periodic_update(self) -> None:
        """Periodically update the dashboard every 1 second."""
        import asyncio
        
        while True:
            await asyncio.sleep(1)
            self._update_display()


class AddAppScreen(Screen):
    """Screen to add a new app."""
    
    def __init__(self, config_mgr: ConfigManager, notify: NotificationManager, callback):
        super().__init__()
        self.config_mgr = config_mgr
        self.notify = notify
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Static("Add New App", id="title")
        yield Label("Package name (e.g., com.instagram.android):")
        yield Input(id="package_input", placeholder="Package name")
        yield Label("App name:")
        yield Input(id="name_input", placeholder="Display name")
        yield Label("Time limit (minutes):")
        yield Input(id="limit_input", placeholder="60")
        yield Horizontal(
            Button("Add", id="btn-add-confirm", variant="primary"),
            Button("Cancel", id="btn-add-cancel", variant="default")
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "btn-add-confirm":
            package = self.query_one("#package_input", Input).value
            name = self.query_one("#name_input", Input).value
            limit_str = self.query_one("#limit_input", Input).value
            
            if not package or not name or not limit_str:
                self.notify.send_custom("Error", "All fields are required")
                return
            
            try:
                limit = int(limit_str)
                if limit <= 0:
                    self.notify.send_custom("Error", "Limit must be positive")
                    return
                
                if self.config_mgr.add_app(package, name, limit):
                    self.notify.send_custom("Success", f"Added {name}")
                    self.callback()
                    self.app.pop_screen()
                else:
                    self.notify.send_custom("Error", "App already exists")
            except ValueError:
                self.notify.send_custom("Error", "Invalid limit value")
        
        elif button_id == "btn-add-cancel":
            self.app.pop_screen()


class SetTimerScreen(Screen):
    """Screen to set timer for an app."""
    
    def __init__(self, config_mgr: ConfigManager, notify: NotificationManager, callback):
        super().__init__()
        self.config_mgr = config_mgr
        self.notify = notify
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Static("Set Timer", id="title")
        yield Label("Package name:")
        yield Input(id="package_input", placeholder="com.example.app")
        yield Label("New limit (minutes):")
        yield Input(id="limit_input", placeholder="60")
        yield Horizontal(
            Button("Update", id="btn-set-confirm", variant="primary"),
            Button("Cancel", id="btn-set-cancel", variant="default")
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "btn-set-confirm":
            package = self.query_one("#package_input", Input).value
            limit_str = self.query_one("#limit_input", Input).value
            
            if not package or not limit_str:
                self.notify.send_custom("Error", "All fields are required")
                return
            
            try:
                limit = int(limit_str)
                if limit <= 0:
                    self.notify.send_custom("Error", "Limit must be positive")
                    return
                
                if self.config_mgr.update_app_limit(package, limit):
                    self.notify.send_custom("Success", f"Updated limit to {limit}m")
                    self.callback()
                    self.app.pop_screen()
                else:
                    self.notify.send_custom("Error", "App not found")
            except ValueError:
                self.notify.send_custom("Error", "Invalid limit value")
        
        elif button_id == "btn-set-cancel":
            self.app.pop_screen()


class ManageAppsScreen(Screen):
    """Screen to manage apps."""
    
    def __init__(self, config_mgr: ConfigManager, monitor: AppMonitor, 
                 notify: NotificationManager, callback):
        super().__init__()
        self.config_mgr = config_mgr
        self.monitor = monitor
        self.notify = notify
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Static("Manage Apps", id="title")
        yield DataTable(id="manage-table")
        yield Label("Options: D - Delete | E - Enable/Disable | R - Reset | B - Back")
        yield Horizontal(
            Button("Delete", id="btn-delete", variant="error"),
            Button("Toggle", id="btn-toggle", variant="default"),
            Button("Reset", id="btn-reset", variant="default"),
            Button("Back", id="btn-back", variant="default")
        )
    
    def on_mount(self) -> None:
        table = self.query_one("#manage-table", DataTable)
        table.add_columns("App", "Limit", "Used", "Enabled", "Action")
        
        apps = self.config_mgr.get_all_apps()
        for package, app_data in apps.items():
            used = self.config_mgr.get_total_usage(package)
            limit = app_data["limit_minutes"]
            enabled = "Yes" if app_data["enabled"] else "No"
            action = app_data["action"]
            
            table.add_row(app_data["name"], f"{limit}m", f"{used}m", enabled, action)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "btn-back":
            self.app.pop_screen()
            self.callback()
        elif button_id == "btn-delete":
            self.notify.send_custom("Info", "Select an app first (arrow keys + Enter)")
        elif button_id == "btn-toggle":
            self.notify.send_custom("Info", "Select an app first (arrow keys + Enter)")
        elif button_id == "btn-reset":
            self.notify.send_custom("Info", "Select an app first (arrow keys + Enter)")


class ListInstalledAppsScreen(Screen):
    """Screen showing all installed apps on device."""
    
    def __init__(self, adb: ADBHandler, config_mgr: ConfigManager, notify: NotificationManager):
        super().__init__()
        self.adb = adb
        self.config_mgr = config_mgr
        self.notify = notify
        self.installed_apps = []
    
    def compose(self) -> ComposeResult:
        yield Static("📱 Installed Apps on Device", id="title")
        yield Static("Loading installed apps...", id="loading")
        yield DataTable(id="apps-list-table")
        yield Label("A - Add Selected | Q - Back")
        yield Horizontal(
            Button("Add Selected", id="btn-add-selected", variant="primary"),
            Button("Back", id="btn-back-list", variant="default")
        )
    
    def on_mount(self) -> None:
        """Load installed apps when screen mounts."""
        self._load_apps()
    
    @work(exclusive=True)
    async def _load_apps(self) -> None:
        """Load installed apps from device."""
        import asyncio
        loading = self.query_one("#loading", Static)
        loading.update("Loading apps from device...")
        
        await asyncio.sleep(0.5)
        self.installed_apps = self.adb.get_installed_apps()
        
        if not self.installed_apps:
            loading.update("⚠ No apps found or device not available")
            return
        
        # Hide loading message
        loading.visible = False
        
        # Setup table
        table = self.query_one("#apps-list-table", DataTable)
        table.add_columns("App Name", "Package", "Status")
        
        # Get monitored apps
        monitored = set(self.config_mgr.get_all_apps().keys())
        
        # Add apps to table
        for app in self.installed_apps:
            name = app.get("name", "Unknown")
            package = app.get("package", "")
            status = "✓ Monitoring" if package in monitored else "○ Not monitored"
            table.add_row(name, package, status)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn-back-list":
            self.app.pop_screen()
        elif button_id == "btn-add-selected":
            self.action_add_selected()
    
    def action_add_selected(self) -> None:
        """Add selected app to monitor."""
        try:
            table = self.query_one("#apps-list-table", DataTable)
            if not table.row_count:
                self.notify.send_custom("Error", "No apps available")
                return
            
            row_idx = table.cursor_row
            if row_idx >= 0 and row_idx < len(self.installed_apps):
                app = self.installed_apps[row_idx]
                package = app.get("package")
                name = app.get("name", package)
                
                if self.config_mgr.get_app(package):
                    self.notify.send_custom("Info", f"{name} already monitoring")
                    return
                
                self.app.push_screen(AddAppLimitScreen(
                    self.config_mgr, 
                    self.notify, 
                    package, 
                    name,
                    self._refresh
                ))
        except Exception as e:
            self.notify.send_custom("Error", f"Error: {str(e)[:50]}")
    
    def _refresh(self) -> None:
        """Refresh after adding app."""
        self.app.pop_screen()


class AddAppLimitScreen(Screen):
    """Screen to input limit for a new app from installed list."""
    
    def __init__(self, config_mgr: ConfigManager, notify: NotificationManager, 
                 package: str, name: str, callback):
        super().__init__()
        self.config_mgr = config_mgr
        self.notify = notify
        self.package = package
        self.name = name
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Static(f"Set Limit for {self.name}", id="title")
        yield Label(f"Package: {self.package}")
        yield Label("Time limit (minutes):")
        yield Input(id="limit_input", placeholder="60")
        yield Horizontal(
            Button("Add", id="btn-confirm", variant="primary"),
            Button("Cancel", id="btn-cancel", variant="default")
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn-confirm":
            limit_str = self.query_one("#limit_input", Input).value
            
            try:
                limit = int(limit_str)
                if limit <= 0:
                    self.notify.send_custom("Error", "Limit must be positive")
                    return
                
                if self.config_mgr.add_app(self.package, self.name, limit):
                    self.notify.send_custom("Success", f"Added {self.name} - {limit}m")
                    self.callback()
                    self.app.pop_screen()
                else:
                    self.notify.send_custom("Error", "Failed to add app")
            except ValueError:
                self.notify.send_custom("Error", "Invalid limit")
        
        elif button_id == "btn-cancel":
            self.app.pop_screen()


def run_interactive(config_mgr: ConfigManager, adb: ADBHandler,
                   monitor: AppMonitor, notify: NotificationManager):
    """Run interactive Textual dashboard."""
    from textual.app import App
    
    class TimerApp(App):
        CSS = """
        Screen {
            background: $surface;
            color: $text;
        }
        
        #title {
            background: $boost;
            color: $text;
            width: 100%;
            text-align: center;
            padding: 1;
            dock: top;
        }
        
        .section-header {
            background: $panel;
            width: 100%;
            padding: 0 1;
        }
        
        #stats-container {
            border: solid $accent;
            width: 100%;
            height: 8;
            padding: 1;
        }
        
        #apps-table {
            width: 100%;
            height: 1fr;
            border: solid $accent;
        }
        
        Horizontal {
            margin: 1 2;
        }
        
        Button {
            margin-right: 1;
        }
        """
        
        def on_mount(self) -> None:
            self.push_screen(DashboardScreen(config_mgr, adb, monitor, notify))
    
    app = TimerApp()
    
    # Start monitoring if not already running
    if not monitor.is_running():
        monitor.start()
        notify.send_monitoring_started(len(config_mgr.get_all_apps()))
    
    try:
        app.run()
    finally:
        if monitor.is_running():
            monitor.stop()
            notify.send_monitoring_stopped()
