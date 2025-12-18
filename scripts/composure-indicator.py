#!/usr/bin/env python3
"""
Composure Indicator - System tray service for Composure
Runs in background, provides tray menu, watches for new screenshots.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Gio', '2.0')

from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3, GLib, Gio
import subprocess
import os
import sys
import json
import time
from pathlib import Path


class ComposureIndicator:
    """System tray indicator for Composure."""
    
    ICON_NAME = "camera-photo-symbolic"
    APP_ID = "composure-indicator"
    
    def __init__(self):
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / 'config.json'
        self._config = self._load_config()
        
        # Get script directory to find main app
        self._script_dir = Path(__file__).parent.parent
        
        # Screenshot directory to watch
        self._screenshot_dir = Path.home() / 'Pictures' / 'Screenshots'
        
        # Create indicator
        self._indicator = AppIndicator3.Indicator.new(
            self.APP_ID,
            self.ICON_NAME,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_title("Composure")
        
        # Build menu
        self._build_menu()
        
        # Start file monitor
        self._start_file_monitor()
        
    def _get_config_dir(self) -> Path:
        """Get config directory."""
        config_dir = Path(os.environ.get('XDG_CONFIG_HOME', 
                                          Path.home() / '.config'))
        return config_dir / 'composure'
        
    def _load_config(self) -> dict:
        """Load configuration."""
        default = {
            'shortcuts': {
                'capture-selection': 'Print',
                'capture-window': '<Alt>Print',
                'capture-screen': '<Shift>Print',
            }
        }
        
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as f:
                    saved = json.load(f)
                    default.update(saved)
            except Exception as e:
                print(f"Failed to load config: {e}")
                
        return default
        
    def _build_menu(self):
        """Build the indicator menu."""
        menu = Gtk.Menu()
        
        # Status
        status_item = Gtk.MenuItem(label="✓ Watching for screenshots")
        status_item.set_sensitive(False)
        menu.append(status_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Open main app
        open_item = Gtk.MenuItem(label="Open Composure")
        open_item.connect("activate", self._on_open)
        menu.append(open_item)
        
        # Preferences
        prefs_item = Gtk.MenuItem(label="Preferences")
        prefs_item.connect("activate", self._on_preferences)
        menu.append(prefs_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # About
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self._on_about)
        menu.append(about_item)
        
        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)
        
        menu.show_all()
        self._indicator.set_menu(menu)
        
    def _start_file_monitor(self):
        """Start watching the Screenshots folder for new files."""
        # Ensure directory exists
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file monitor
        gfile = Gio.File.new_for_path(str(self._screenshot_dir))
        self._monitor = gfile.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self._monitor.connect("changed", self._on_file_changed)
        print(f"Watching {self._screenshot_dir} for new screenshots...")
        
    def _on_file_changed(self, monitor, file, other_file, event_type):
        """Handle file system changes."""
        if event_type == Gio.FileMonitorEvent.CREATED:
            path = file.get_path()
            if path and path.lower().endswith(('.png', '.jpg', '.jpeg')):
                print(f"New screenshot detected: {path}")
                # Small delay to ensure file is fully written
                GLib.timeout_add(500, self._launch_with_file, path)
                
    def _launch_with_file(self, filepath):
        """Launch Composure with a specific file."""
        try:
            subprocess.Popen(
                ['python3', '-m', 'src.main', filepath],
                cwd=str(self._script_dir),
                start_new_session=True
            )
        except Exception as e:
            print(f"Failed to launch Composure: {e}")
        return False  # Don't repeat
        
    def _launch_composure(self):
        """Launch main Composure application."""
        try:
            subprocess.Popen(
                ['python3', '-m', 'src.main'],
                cwd=str(self._script_dir),
                start_new_session=True
            )
        except Exception as e:
            print(f"Failed to launch Composure: {e}")
        return False
            
    def _on_open(self, item):
        """Handle open menu item."""
        self._launch_composure()
        
    def _on_preferences(self, item):
        """Handle preferences menu item."""
        self._launch_composure()
        
    def _on_about(self, item):
        """Show about dialog."""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Composure")
        dialog.set_version("0.1.0")
        dialog.set_comments("Screenshot Beautifier for Linux\n\nWatching ~/Pictures/Screenshots")
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.run()
        dialog.destroy()
        
    def _on_quit(self, item):
        """Quit the indicator."""
        Gtk.main_quit()
        
    def run(self):
        """Start the indicator."""
        print("Composure indicator running...")
        print("Take a screenshot with your system tool - Composure will open automatically!")
        Gtk.main()


def main():
    """Entry point."""
    indicator = ComposureIndicator()
    indicator.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
