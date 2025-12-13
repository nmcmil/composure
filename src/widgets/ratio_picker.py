"""Ratio and size picker widget."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from typing import Callable, Optional

from ..models.composition import RATIO_PRESETS, PLATFORM_PRESETS


class RatioPicker(Gtk.Box):
    """Widget for selecting output aspect ratio or platform size."""
    
    def __init__(self, on_change: Optional[Callable[[str, tuple, tuple, str], None]] = None):
        """
        Args:
            on_change: Callback(mode, ratio, size_px, platform)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        self._on_change = on_change
        self._current_mode = 'autoRatio'
        self._custom_size = (1920, 1080)
        
        # Section label
        label = Gtk.Label(label="Output Size")
        label.set_halign(Gtk.Align.START)
        label.add_css_class('section-title')
        self.append(label)
        
        # Mode dropdown
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        mode_store = Gtk.StringList()
        mode_store.append("Auto")
        mode_store.append("Ratio")
        mode_store.append("Platform")
        mode_store.append("Custom")
        
        self._mode_dropdown = Gtk.DropDown(model=mode_store)
        self._mode_dropdown.set_hexpand(True)
        self._mode_dropdown.connect('notify::selected', self._on_mode_changed)
        mode_box.append(self._mode_dropdown)
        
        self.append(mode_box)
        
        # Stack for different mode options
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        
        # Auto page (empty or just info)
        auto_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        auto_label = Gtk.Label(label="Matches source aspect ratio")
        auto_label.add_css_class('dim-label')
        auto_label.set_halign(Gtk.Align.START)
        auto_box.append(auto_label)
        self._stack.add_named(auto_box, 'auto')
        
        # Ratio page
        ratio_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ratio_box.set_margin_top(8)
        
        ratio_store = Gtk.StringList()
        for rid, preset in RATIO_PRESETS.items():
            if rid != 'auto':
                ratio_store.append(preset['name'])
                
        self._ratio_dropdown = Gtk.DropDown(model=ratio_store)
        self._ratio_dropdown.set_hexpand(True)
        self._ratio_dropdown.connect('notify::selected', self._on_ratio_changed)
        ratio_box.append(self._ratio_dropdown)
        self._stack.add_named(ratio_box, 'ratio')
        
        # Platform page
        platform_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        platform_box.set_margin_top(8)
        
        platform_store = Gtk.StringList()
        self._platform_ids = []
        for pid, preset in PLATFORM_PRESETS.items():
            platform_store.append(f"{preset['name']} ({preset['width']}×{preset['height']})")
            self._platform_ids.append(pid)
            
        self._platform_dropdown = Gtk.DropDown(model=platform_store)
        self._platform_dropdown.set_hexpand(True)
        self._platform_dropdown.connect('notify::selected', self._on_platform_changed)
        platform_box.append(self._platform_dropdown)
        self._stack.add_named(platform_box, 'platform')
        
        # Custom size page
        custom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_box.set_margin_top(8)
        
        self._width_entry = Gtk.SpinButton.new_with_range(100, 8000, 10)
        self._width_entry.set_value(1920)
        self._width_entry.set_width_chars(6)
        self._width_entry.connect('value-changed', self._on_custom_size_changed)
        custom_box.append(self._width_entry)
        
        custom_box.append(Gtk.Label(label="×"))
        
        self._height_entry = Gtk.SpinButton.new_with_range(100, 8000, 10)
        self._height_entry.set_value(1080)
        self._height_entry.set_width_chars(6)
        self._height_entry.connect('value-changed', self._on_custom_size_changed)
        custom_box.append(self._height_entry)
        
        custom_box.append(Gtk.Label(label="px"))
        
        self._stack.add_named(custom_box, 'custom')
        
        # Set default
        self._stack.set_visible_child_name('auto')
        self.append(self._stack)
        
    def _on_mode_changed(self, dropdown, pspec) -> None:
        """Handle mode dropdown change."""
        selected = dropdown.get_selected()
        
        modes = ['auto', 'ratio', 'platform', 'custom']
        mode_mapping = ['autoRatio', 'fixedRatio', 'platform', 'fixedSize']
        
        if 0 <= selected < len(modes):
            self._stack.set_visible_child_name(modes[selected])
            self._current_mode = mode_mapping[selected]
            self._emit_change()
            
    def _on_ratio_changed(self, dropdown, pspec) -> None:
        """Handle ratio dropdown change."""
        self._emit_change()
        
    def _on_platform_changed(self, dropdown, pspec) -> None:
        """Handle platform dropdown change."""
        self._emit_change()
        
    def _on_custom_size_changed(self, spin) -> None:
        """Handle custom size change."""
        self._emit_change()
        
    def _emit_change(self) -> None:
        """Emit change callback."""
        if not self._on_change:
            return
            
        mode = self._current_mode
        ratio = (16, 9)
        size_px = (1920, 1080)
        platform = None
        
        if mode == 'fixedRatio':
            idx = self._ratio_dropdown.get_selected()
            ratio_ids = [rid for rid in RATIO_PRESETS.keys() if rid != 'auto']
            if 0 <= idx < len(ratio_ids):
                ratio_data = RATIO_PRESETS[ratio_ids[idx]]
                if ratio_data['ratio']:
                    ratio = ratio_data['ratio']
                    
        elif mode == 'platform':
            idx = self._platform_dropdown.get_selected()
            if 0 <= idx < len(self._platform_ids):
                platform = self._platform_ids[idx]
                preset = PLATFORM_PRESETS[platform]
                size_px = (preset['width'], preset['height'])
                
        elif mode == 'fixedSize':
            size_px = (
                int(self._width_entry.get_value()),
                int(self._height_entry.get_value())
            )
            
        self._on_change(mode, ratio, size_px, platform)
        
    def set_mode(self, mode: str) -> None:
        """Set the current mode."""
        mode_mapping = {
            'autoRatio': 0,
            'fixedRatio': 1,
            'platform': 2,
            'fixedSize': 3
        }
        if mode in mode_mapping:
            self._mode_dropdown.set_selected(mode_mapping[mode])
