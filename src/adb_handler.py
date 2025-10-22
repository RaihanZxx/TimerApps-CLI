import subprocess
import re
from typing import List, Optional, Tuple
from .utils import log_message


class ADBHandler:
    """Handle ADB and Root commands for app management."""
    
    def __init__(self, use_root: bool = False):
        self.use_root = use_root
        self.device_id: Optional[str] = None
        self._detect_device()
        self.is_available = self._check_availability()
    
    def _run_command(self, cmd: List[str], use_root: bool = False, shell: bool = False) -> Tuple[bool, str]:
        """Execute shell command and return (success, output)."""
        try:
            if use_root:
                # Convert list to shell string and prepend 'su'
                cmd_str = " ".join(cmd)
                cmd = ["su", "-c", cmd_str]
                shell = False
            elif shell:
                # Convert list to string for shell execution
                cmd = " ".join(cmd)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=shell
            )
            
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            log_message(f"Command timeout: {cmd}", "ERROR")
            return False, ""
        except FileNotFoundError as e:
            log_message(f"Command not found: {e}", "ERROR")
            return False, ""
        except Exception as e:
            log_message(f"Command error: {e}", "ERROR")
            return False, ""
    
    def _detect_device(self) -> None:
        """Auto-detect and select first available device."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=3  # Shorter timeout for faster CLI
            )
            
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip() and "List of devices" not in line:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "device":
                        self.device_id = parts[0]
                        log_message(f"Device selected: {self.device_id}")
                        return
        except subprocess.TimeoutExpired:
            log_message("Device detection timeout - continuing anyway", "WARNING")
        except Exception as e:
            log_message(f"Failed to detect device: {e}", "WARNING")
    
    def _adb_shell(self, cmd_str: str) -> Tuple[bool, str]:
        """Execute command on device via ADB shell."""
        try:
            # Use specific device if available
            cmd = ["adb"]
            if self.device_id:
                cmd.extend(["-s", self.device_id])
            cmd.extend(["shell", cmd_str])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check for authorization errors
            if "unauthorized" in result.stderr.lower() or "permission denied" in result.stderr.lower():
                log_message("[ERROR] ADB device unauthorized - tap 'Allow' on your Android device!", "ERROR")
                return False, ""
            
            if "error" in result.stderr.lower() and result.returncode != 0:
                log_message(f"[DEBUG] ADB shell stderr: {result.stderr}", "ERROR")
            
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            log_message(f"ADB shell error: {e}", "ERROR")
            return False, ""
    
    def _check_availability(self) -> bool:
        """Check if ADB or Root is available."""
        if self.use_root:
            success, _ = self._run_command(["su", "-c", "id"], use_root=True)
            return success
        else:
            if self.device_id:
                return True  # Device already detected
            else:
                log_message("[WARNING] No ADB device detected")
                return False
    
    def get_active_app(self) -> Optional[str]:
        """Get currently active app package name."""
        try:
            if self.use_root:
                # Try activity first (more reliable), fallback to window
                cmd1 = "dumpsys activity activities | grep mCurrentFocus"
                success, output = self._run_command([cmd1], use_root=True, shell=True)
                if not success or not output:
                    cmd2 = "dumpsys window windows | grep mCurrentFocus"
                    success, output = self._run_command([cmd2], use_root=True, shell=True)
            else:
                # Try activity first (more reliable), fallback to window
                success, output = self._adb_shell("dumpsys activity activities | grep mCurrentFocus")
                if not success or not output:
                    success, output = self._adb_shell("dumpsys window windows | grep mCurrentFocus")
            
            if not success or not output:
                return None
            
            # Parse all lines to find mCurrentFocus
            for line in output.split("\n"):
                if "mCurrentFocus" not in line:
                    continue
                
                # Parse output: mCurrentFocus=Window{...u0 com.package.name/...}
                try:
                    # Look for package pattern: com.something.something
                    match = re.search(r"(com\.[a-zA-Z0-9._]+)", line)
                    if match:
                        return match.group(1)
                    
                    # Fallback: split by u0 and extract package
                    if "u0 " in line:
                        parts = line.split("u0 ")
                        if len(parts) > 1:
                            package_part = parts[1].split("/")[0].split(" ")[0]
                            return package_part.strip()
                except (IndexError, ValueError):
                    pass
            
            return None
        except Exception as e:
            log_message(f"Error getting active app: {e}", "ERROR")
            return None
    
    def get_installed_apps(self) -> List[dict]:
        """Get list of installed apps with names."""
        try:
            if self.use_root:
                cmd = ["pm", "list", "packages", "-3"]
                success, output = self._run_command(cmd, use_root=True)
            else:
                success, output = self._adb_shell("pm list packages -3")
            
            if not success:
                return []
            
            apps = []
            for line in output.split("\n"):
                line = line.strip()
                if line.startswith("package:"):
                    package = line.replace("package:", "").strip()
                    apps.append({
                        "package": package,
                        "name": self.get_app_name(package),
                    })
            
            return apps
        except Exception as e:
            log_message(f"Error getting installed apps: {e}", "ERROR")
            return []
    
    def get_app_name(self, package: str) -> str:
        """Get human-readable app name from device."""
        try:
            if self.use_root:
                cmd = f"pm dump {package} | grep label="
                success, output = self._run_command([cmd], use_root=True, shell=True)
            else:
                success, output = self._adb_shell(f"pm dump {package} | grep label=")
            
            if success and "label=" in output:
                # Extract label value
                try:
                    label = output.split("label=")[1].split(" ")[0]
                    return label.strip("'\"")
                except (IndexError, ValueError):
                    pass
            
            return package.split(".")[-1].capitalize()
        except Exception:
            return package.split(".")[-1].capitalize()
    
    def kill_app(self, package: str) -> bool:
        """Force-stop (kill) an app."""
        try:
            if self.use_root:
                cmd = ["am", "force-stop", package]
                success, _ = self._run_command(cmd, use_root=True)
            else:
                success, _ = self._adb_shell(f"am force-stop {package}")
            
            if success:
                log_message(f"Killed app: {package}")
            else:
                log_message(f"Failed to kill app: {package}", "ERROR")
            
            return success
        except Exception as e:
            log_message(f"Error killing app {package}: {e}", "ERROR")
            return False
    
    def freeze_app(self, package: str) -> bool:
        """Disable (freeze) an app."""
        try:
            if self.use_root:
                cmd = ["pm", "disable-user", "--user", "0", package]
                success, _ = self._run_command(cmd, use_root=True)
            else:
                success, _ = self._adb_shell(f"pm disable-user --user 0 {package}")
            
            if success:
                log_message(f"Froze app: {package}")
            else:
                log_message(f"Failed to freeze app: {package}", "ERROR")
            
            return success
        except Exception as e:
            log_message(f"Error freezing app {package}: {e}", "ERROR")
            return False
    
    def unfreeze_app(self, package: str) -> bool:
        """Re-enable (unfreeze) a disabled app."""
        try:
            if self.use_root:
                cmd = ["pm", "enable", "--user", "0", package]
                success, _ = self._run_command(cmd, use_root=True)
            else:
                success, _ = self._adb_shell(f"pm enable --user 0 {package}")
            
            if success:
                log_message(f"Unfroze app: {package}")
            else:
                log_message(f"Failed to unfreeze app: {package}", "ERROR")
            
            return success
        except Exception as e:
            log_message(f"Error unfreezing app {package}: {e}", "ERROR")
            return False
    
    def is_app_running(self, package: str) -> bool:
        """Check if app is currently running."""
        try:
            if self.use_root:
                cmd = ["pidof", package]
                success, output = self._run_command(cmd, use_root=True)
            else:
                success, output = self._adb_shell(f"pidof {package}")
            
            return success and output.strip() != ""
        except Exception:
            return False
    
    def detect_root(self) -> bool:
        """Auto-detect if device is rooted."""
        try:
            cmd = ["su", "-c", "id"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                input="exit\n"
            )
            
            is_rooted = result.returncode == 0
            log_message(f"Device rooted: {is_rooted}")
            return is_rooted
        except Exception:
            log_message("Device not rooted (or su command failed)")
            return False
