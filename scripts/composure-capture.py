#!/usr/bin/env python3
"""
Composure Capture - One-step screenshot and beautify

Ctrl+Shift+A → Shift+Print via ydotool (Full Screen)
Ctrl+Shift+B → Portal Interactive (Selection)
Ctrl+Shift+C → Alt+Print via ydotool (Window)

Mixed approach for maximum reliability:
- ydotool used for direct capture modes (Window/Desktop)
- Portal used for interactive selection (since it supports it natively)
"""

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

import subprocess
import sys
import os
import time
import random
import string
from pathlib import Path
from urllib.parse import unquote

COMPOSURE_DIR = Path("/home/nick/.gemini/antigravity/Composure")
PICTURES_DIR = Path.home() / "Pictures" / "Screenshots"


def get_latest_screenshot():
    """Get the most recent screenshot."""
    if not PICTURES_DIR.exists():
        PICTURES_DIR.mkdir(parents=True, exist_ok=True)
        return None, 0
    screenshots = list(PICTURES_DIR.glob("Screenshot*.png"))
    if not screenshots:
        return None, 0
    latest = max(screenshots, key=os.path.getmtime)
    return str(latest), os.path.getmtime(latest)


class PortalCapture:
    """XDG Portal screenshot capture."""
    
    def __init__(self):
        self.loop = GLib.MainLoop()
        self.captured_file = None
        self.bus = None
        self.subscription_id = None
        
    def capture(self):
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            token = ''.join(random.choices(string.ascii_lowercase, k=8))
            sender = self.bus.get_unique_name()
            sender_name = sender.lstrip(':').replace('.', '_')
            handle_path = f"/org/freedesktop/portal/desktop/request/{sender_name}/{token}"
            
            self.subscription_id = self.bus.signal_subscribe(
                "org.freedesktop.portal.Desktop",
                "org.freedesktop.portal.Request",
                "Response",
                handle_path,
                None,
                Gio.DBusSignalFlags.NO_MATCH_RULE,
                self._on_response,
                None
            )
            
            proxy = Gio.DBusProxy.new_sync(
                self.bus, Gio.DBusProxyFlags.NONE, None,
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Screenshot",
                None
            )
            
            # Interactive=True to show UI for selection
            params = GLib.Variant.parse(
                GLib.VariantType.new('(sa{sv})'),
                f"('', {{'handle_token': <'{token}'>, 'modal': <true>, 'interactive': <true>}})",
                None, None
            )
            
            proxy.call_sync("Screenshot", params, Gio.DBusCallFlags.NONE, -1, None)
            GLib.timeout_add_seconds(120, self._on_timeout)
            self.loop.run()
            return self.captured_file
        except:
            return None
        finally:
            if self.subscription_id and self.bus:
                self.bus.signal_unsubscribe(self.subscription_id)
                
    def _on_response(self, connection, sender, path, interface, signal, params, user_data):
        try:
            response_code = params.get_child_value(0).get_uint32()
            if response_code == 0:
                results = params.get_child_value(1)
                uri_variant = results.lookup_value("uri", GLib.VariantType.new("s"))
                if uri_variant:
                    uri = uri_variant.get_string()
                    self.captured_file = unquote(uri[7:] if uri.startswith("file://") else uri)
        except:
            pass
        self.loop.quit()
        
    def _on_timeout(self):
        if self.loop.is_running():
            self.loop.quit()
        return False


def capture_with_ydotool(key_combination):
    """Capture using ydotool key simulation."""
    _, before_time = get_latest_screenshot()
    
    # Trigger keys via ydotool
    try:
        subprocess.run(["ydotool", "key", key_combination], capture_output=True, timeout=3)
    except Exception:
        return None
    
    # Wait for screenshot
    for _ in range(60):
        time.sleep(0.3)
        latest, mtime = get_latest_screenshot()
        if latest and mtime > before_time:
            time.sleep(0.3)
            return latest
    return None


def launch_composure(image_path):
    """Launch Composure."""
    os.chdir(COMPOSURE_DIR)
    subprocess.run(["pkill", "-f", "python3 -m src.main"],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    time.sleep(0.3)
    subprocess.Popen([sys.executable, "-m", "src.main", image_path],
                     start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def notify(message, icon=None):
    cmd = ["notify-send"]
    if icon and os.path.exists(icon):
        cmd.extend(["-i", icon])
    cmd.extend(["Composure", message])
    subprocess.run(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "selection"
    
    captured = None
    
    if mode == "window":
        # Alt+SysRq (Window) - Proven to work
        captured = capture_with_ydotool("alt+sysrq")
        
    elif mode == "desktop":
        # Use Portal for desktop too - clearer UI and more reliable than ydotool shift+sysrq
        portal = PortalCapture()
        captured = portal.capture()
        
    else: # selection
        # Use Portal for selection - robust interactive UI
        portal = PortalCapture()
        captured = portal.capture()
    
    if captured and os.path.exists(captured):
        notify("Opening screenshot editor...", captured)
        launch_composure(captured)
        sys.exit(0)
    else:
        notify("Screenshot cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()
