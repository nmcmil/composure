"""Preferences dialog."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk
from typing import Optional

from ..config import ConfigManager

class PreferencesDialog(Adw.PreferencesWindow):
    """Application preferences dialog."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("Preferences")
        self.set_default_size(500, 400)
        self.set_modal(True)
        
        self._config = ConfigManager()
        
        # Shortcuts Page
        page = Adw.PreferencesPage(
            title="Settings",
            icon_name="preferences-system-symbolic"
        )
        self.add(page)
        
        # Info Group - explain how it works
        info_group = Adw.PreferencesGroup(
            title="How It Works",
            description="Composure watches ~/Pictures/Screenshots for new files. "
                       "When you take a screenshot with your system tool (Print key), "
                       "Composure automatically opens with that image."
        )
        page.add(info_group)
        
        # Actions Group - just copy/save shortcuts
        actions_group = Adw.PreferencesGroup(
            title="Keyboard Shortcuts",
            description="These shortcuts work when Composure is open."
        )
        page.add(actions_group)
        
        self._add_shortcut_row(
            actions_group,
            "Copy to Clipboard",
            "copy"
        )
        self._add_shortcut_row(
            actions_group,
            "Copy and Close",
            "copy-and-close"
        )
        
        # Startup Group
        startup_group = Adw.PreferencesGroup(title="Startup")
        page.add(startup_group)
        
        startup_row = Adw.ActionRow(
            title="Launch at Login",
            subtitle="Start Composure indicator when you log in"
        )
        
        self._startup_switch = Gtk.Switch()
        self._startup_switch.set_valign(Gtk.Align.CENTER)
        self._startup_switch.set_active(self._is_autostart_enabled())
        self._startup_switch.connect("notify::active", self._on_startup_toggled)
        
        startup_row.add_suffix(self._startup_switch)
        startup_group.add(startup_row)
        
    def _is_autostart_enabled(self) -> bool:
        """Check if autostart is enabled."""
        import os
        from pathlib import Path
        autostart_file = Path.home() / '.config' / 'autostart' / 'composure-indicator.desktop'
        return autostart_file.exists()
        
    def _on_startup_toggled(self, switch, pspec):
        """Handle startup toggle."""
        import os
        from pathlib import Path
        
        autostart_dir = Path.home() / '.config' / 'autostart'
        autostart_file = autostart_dir / 'composure-indicator.desktop'
        
        if switch.get_active():
            # Enable autostart
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            # Find indicator script
            script_path = Path(__file__).parent.parent.parent / 'scripts' / 'composure-indicator.py'
            
            desktop_content = f'''[Desktop Entry]
Type=Application
Name=Composure Indicator
Comment=Screenshot beautifier system tray
Exec=python3 {script_path}
Icon=camera-photo-symbolic
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
'''
            autostart_file.write_text(desktop_content)
        else:
            # Disable autostart
            if autostart_file.exists():
                autostart_file.unlink()
        
    def _add_shortcut_row(self, group: Adw.PreferencesGroup, title: str, action_name: str):
        """Add a shortcut configuration row."""
        row = Adw.ActionRow(title=title)
        
        shortcut_label = Gtk.ShortcutLabel()
        shortcut_label.set_accelerator(self._config.get_shortcut(action_name))
        
        # Edit button
        btn = Gtk.Button(icon_name="document-edit-symbolic")
        btn.add_css_class("flat")
        btn.set_tooltip_text("Edit shortcut")
        
        btn.connect("clicked", self._on_edit_clicked, action_name, shortcut_label)
        
        row.add_suffix(shortcut_label)
        row.add_suffix(btn)
        group.add(row)
        
    def _on_edit_clicked(self, btn: Gtk.Button, action_name: str, shortcut_label: Gtk.ShortcutLabel):
        """Handle edit button click."""
        def on_shortcut_set(accelerator):
            self._config.set_shortcut(action_name, accelerator)
            shortcut_label.set_accelerator(accelerator)
        
        dialog = KeyCaptureDialog(self, on_shortcut_set)
        dialog.present()

class KeyCaptureDialog(Adw.Window):
    """Window to capture a single key combination."""
    
    def __init__(self, parent, callback, **kwargs):
        super().__init__(transient_for=parent, modal=True, **kwargs)
        self.set_default_size(350, 200)
        self.set_title("Set Shortcut")
        
        self._accelerator = None
        self._callback = callback
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(False)
        header.set_show_start_title_buttons(False)
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda b: self.close())
        header.pack_start(cancel_btn)
        
        self._set_btn = Gtk.Button(label="Set")
        self._set_btn.add_css_class("suggested-action")
        self._set_btn.set_sensitive(False)
        self._set_btn.connect("clicked", self._on_set_clicked)
        header.pack_end(self._set_btn)
        
        main_box.append(header)
        
        # Content area
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_margin_top(32)
        content.set_margin_bottom(32)
        content.set_margin_start(32)
        content.set_margin_end(32)
        content.set_vexpand(True)
        content.set_valign(Gtk.Align.CENTER)
        
        lbl = Gtk.Label(label="Press the new shortcut keys...")
        lbl.add_css_class("title-2")
        content.append(lbl)
        
        self._shortcut_label = Gtk.ShortcutLabel()
        self._shortcut_label.set_disabled_text("Waiting for input...")
        self._shortcut_label.set_halign(Gtk.Align.CENTER)
        content.append(self._shortcut_label)
        
        main_box.append(content)
        
        self.set_content(main_box)
        
        # Key controller on the window itself with CAPTURE phase
        key_controller = Gtk.EventControllerKey()
        key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)
        
    def _on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press."""
        # Ignore Escape (let it close the window naturally or handle manually)
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
            
        # Ignore modifiers being pressed alone
        if keyval in [Gdk.KEY_Control_L, Gdk.KEY_Control_R, 
                      Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
                      Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
                      Gdk.KEY_Meta_L, Gdk.KEY_Meta_R,
                      Gdk.KEY_Super_L, Gdk.KEY_Super_R]:
            return False
            
        # Clean up state (remove caps lock indicator)
        state &= ~Gdk.ModifierType.LOCK_MASK
        
        # Get accelerator
        self._accelerator = Gtk.accelerator_name(keyval, state)
        self._shortcut_label.set_accelerator(self._accelerator)
        self._set_btn.set_sensitive(True)
        
        return True
        
    def _on_set_clicked(self, btn):
        """Handle Set button click."""
        if self._callback and self._accelerator:
            self._callback(self._accelerator)
        self.close()
        
    def get_accelerator(self):
        return self._accelerator
