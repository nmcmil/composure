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


class ComposureApplication(Adw.Application):
    """Main application class for Composure."""
    
    def __init__(self):
        super().__init__(
            application_id='io.github.composure',
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        
        self.set_resource_base_path('/io/github/composure')
        
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


def main():
    """Application entry point."""
    app = ComposureApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
