#!/usr/bin/env python3
"""
Composure - Linux Screenshot Beautifier
Main application entry point
"""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk

from .window import ComposureWindow
from .config import ConfigManager


class ComposureApplication(Adw.Application):
    """Main application class for Composure."""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.composure',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        
        self.set_resource_base_path('/io/github/composure')
        self._config = ConfigManager()
        
    def do_startup(self):
        """Called when the application starts."""
        Adw.Application.do_startup(self)
        
        # Set up actions
        self._setup_actions()
        
        # Apply custom CSS
        self._apply_css()
        
    def _setup_actions(self):
        """Set up application actions."""
        # Capture action
        capture_action = Gio.SimpleAction.new('capture', None)
        capture_action.connect('activate', self._on_capture)
        self.add_action(capture_action)
        self.set_accels_for_action('app.capture', ['<Primary>n'])
        
        # Open image action
        open_action = Gio.SimpleAction.new('open', None)
        open_action.connect('activate', self._on_open)
        self.add_action(open_action)
        self.set_accels_for_action('app.open', ['<Primary>o'])
        
        # Copy action
        copy_action = Gio.SimpleAction.new('copy', None)
        copy_action.connect('activate', self._on_copy)
        self.add_action(copy_action)
        self.set_accels_for_action('app.copy', ['<Primary>c'])
        
        # Save action
        save_action = Gio.SimpleAction.new('save', None)
        save_action.connect('activate', self._on_save)
        self.add_action(save_action)
        self.set_accels_for_action('app.save', ['<Primary>s'])
        
        # Quit action
        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self._on_quit)
        self.add_action(quit_action)
        self.set_accels_for_action('app.quit', ['<Primary>q'])
        
        # About action
        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self._on_about)
        self.add_action(about_action)
        
        # Preferences action
        prefs_action = Gio.SimpleAction.new('preferences', None)
        prefs_action.connect('activate', self._on_preferences)
        self.add_action(prefs_action)
        
        # New Capture Actions
        for action_name in ['input-selection', 'input-window', 'input-screen']:
            action = Gio.SimpleAction.new(action_name, None)
            action.connect('activate', self._on_capture)
            self.add_action(action)
            
        # Copy and Close action
        copy_close_action = Gio.SimpleAction.new('copy-and-close', None)
        copy_close_action.connect('activate', self._on_copy_and_close)
        self.add_action(copy_close_action)
        
        # Set accelerators from config
        self._update_accelerators()
        
    def _update_accelerators(self):
        """Update accelerators from config."""
        mapping = {
            'app.capture': 'capture-selection', # Legacy/Default
            'app.input-selection': 'capture-selection',
            'app.input-window': 'capture-window',
            'app.input-screen': 'capture-screen',
            'app.copy': 'copy',
            'app.copy-and-close': 'copy-and-close',
            'app.open': 'open', # Not configurable yet, but key exists if we added it
        }
        
        # Set configurable ones
        for action_base, config_key in mapping.items():
            accel = self._config.get_shortcut(config_key)
            if accel:
                self.set_accels_for_action(action_base, [accel])
        
        # Keep hardcoded ones for now if not in config
        self.set_accels_for_action('app.save', ['<Primary>s'])
        self.set_accels_for_action('app.quit', ['<Primary>q'])
        self.set_accels_for_action('app.open', ['<Primary>o'])
        
    def _apply_css(self):
        """Apply custom CSS styling."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b'''
            .canvas-container {
                background-color: @window_bg_color;
                border-radius: 12px;
            }
            
            .controls-panel {
                padding: 12px;
            }
            
            .preset-button {
                min-width: 48px;
                min-height: 48px;
                border-radius: 8px;
                padding: 4px;
            }
            
            .preset-button:checked {
                outline: 2px solid @accent_color;
                outline-offset: 2px;
            }
            
            .section-title {
                font-weight: bold;
                font-size: 0.9em;
                opacity: 0.7;
            }
        ''')
        
        Gtk.StyleContext.add_provider_for_display(
            self.get_active_window().get_display() if self.get_active_window() else 
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def do_activate(self):
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = ComposureWindow(application=self)
        win.present()
        
    def do_open(self, files, n_files, hint):
        """Handle opening files."""
        self.activate()
        if files:
            win = self.props.active_window
            if win and hasattr(win, 'load_image'):
                win.load_image(files[0].get_path())
                
    def _on_capture(self, action, param):
        """Handle capture action."""
        win = self.props.active_window
        if win and hasattr(win, 'start_capture'):
            win.start_capture()
            
    def _on_open(self, action, param):
        """Handle open action."""
        win = self.props.active_window
        if win and hasattr(win, 'open_file_dialog'):
            win.open_file_dialog()
            
    def _on_copy(self, action, param):
        """Handle copy action."""
        win = self.props.active_window
        if win and hasattr(win, 'copy_to_clipboard'):
            win.copy_to_clipboard()
            
    def _on_copy_and_close(self, action, param):
        """Handle copy and close action."""
        win = self.props.active_window
        if win and hasattr(win, 'copy_to_clipboard'):
            win.copy_to_clipboard(callback=lambda: self.quit())
            
    def _on_save(self, action, param):
        """Handle save action."""
        win = self.props.active_window
        if win and hasattr(win, 'save_image'):
            win.save_image()
            
    def _on_quit(self, action, param):
        """Handle quit action."""
        self.quit()
        
    def _on_about(self, action, param):
        """Show about dialog."""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="Composure",
            application_icon="image-x-generic",
            version="0.1.0",
            developer_name="@nmcmil",
            license_type=Gtk.License.GPL_3_0,
            comments="Linux Screenshot Beautifier\n\nCapture screenshots and compose them with pleasing backgrounds, shadows, and rounded corners.",
            website="https://github.com/composure"
        )
        about.present()
        
    def _on_preferences(self, action, param):
        """Show preferences dialog."""
        from .widgets.preferences import PreferencesDialog
        win = self.props.active_window
        dialog = PreferencesDialog(transient_for=win)
        dialog.present()
        
        # Refresh accelerators after dialog closes (or ideally during, but simple for now)
        # For now, we rely on the dialog to not need immediate refresh or we can add a signal later.
        # Actually, simpler: just refresh when window closes? 
        # But dialog is modal.
        dialog.connect('close-request', lambda d: self._update_accelerators())


def main():
    """Application entry point."""
    app = ComposureApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
