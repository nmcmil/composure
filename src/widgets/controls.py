"""Main control panel widget."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GObject
from typing import Callable, Optional

from .background_picker import BackgroundPicker
from .ratio_picker import RatioPicker
from ..models.composition import CompositionState
from ..models.preset import PresetManager
from ..config import ConfigManager


class ControlPanel(Gtk.Box):
    """
    Right sidebar control panel with all composition adjustments.
    
    Contains:
    - Preset selector
    - Padding slider
    - Inset slider + Balance toggle
    - Radius slider
    - Shadow slider
    - Background picker
    - Ratio/Size picker
    """
    
    __gsignals__ = {
        'state-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.add_css_class('controls-panel')
        self.set_size_request(280, -1)
        
        self._state = CompositionState()
        self._preset_manager = PresetManager()
        self._config = ConfigManager()
        self._updating = False  # Prevent circular updates
        
        # Scrolled window for controls
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Main content box
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        # Preset section
        content.append(self._create_preset_section())
        content.append(Gtk.Separator())
        
        # Padding slider
        content.append(self._create_slider_row("Padding", 0, 300, 120, self._on_padding_changed))
        
        # Inset section with balance toggle
        content.append(self._create_inset_section())
        
        content.append(Gtk.Separator())
        
        # Radius slider
        content.append(self._create_slider_row("Radius", 0, 50, 18, self._on_radius_changed))
        
        # Shadow slider
        content.append(self._create_slider_row("Shadow", 0, 100, 55, self._on_shadow_changed))
        
        content.append(Gtk.Separator())
        
        # Background picker
        self._background_picker = BackgroundPicker(on_change=self._on_background_changed)
        content.append(self._background_picker)
        
        content.append(Gtk.Separator())
        
        # Ratio picker
        self._ratio_picker = RatioPicker(on_change=self._on_output_changed)
        content.append(self._ratio_picker)
        
        scrolled.set_child(content)
        self.append(scrolled)
        
    def _create_preset_section(self) -> Gtk.Box:
        """Create the preset selector section."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Label
        label = Gtk.Label(label="Preset")
        label.set_halign(Gtk.Align.START)
        label.add_css_class('section-title')
        box.append(label)
        
        # Dropdown + buttons
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Preset dropdown
        self._preset_store = Gtk.StringList()
        self._preset_ids = []
        self._refresh_preset_list()
        
        self._preset_dropdown = Gtk.DropDown(model=self._preset_store)
        self._preset_dropdown.set_hexpand(True)
        self._preset_dropdown.connect('notify::selected', self._on_preset_selected)
        row.append(self._preset_dropdown)
        
        # Save button
        save_btn = Gtk.Button(icon_name='document-save-symbolic')
        save_btn.add_css_class('flat')
        save_btn.set_tooltip_text("Save preset")
        save_btn.connect('clicked', self._on_save_preset)
        row.append(save_btn)
        
        # Set Default button
        self._default_btn = Gtk.Button(icon_name='emblem-favorite-symbolic')
        self._default_btn.add_css_class('flat')
        self._default_btn.set_tooltip_text("Set as default")
        self._default_btn.connect('clicked', self._on_set_default)
        row.append(self._default_btn)
        
        # Delete button
        self._delete_btn = Gtk.Button(icon_name='user-trash-symbolic')
        self._delete_btn.add_css_class('flat')
        self._delete_btn.set_tooltip_text("Delete preset")
        self._delete_btn.connect('clicked', self._on_delete_preset)
        row.append(self._delete_btn)
        
        box.append(row)
        return box
        
    def _refresh_preset_list(self) -> None:
        """Refresh the preset dropdown list."""
        # Clear existing
        while self._preset_store.get_n_items() > 0:
            self._preset_store.remove(0)
        self._preset_ids.clear()
        
        # Add presets
        for preset_id, preset_name in self._preset_manager.list_presets():
            self._preset_store.append(preset_name)
            self._preset_ids.append(preset_id)
            
    def _create_slider_row(self, label: str, min_val: float, max_val: float, 
                           default: float, callback: Callable) -> Gtk.Box:
        """Create a labeled slider row."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Header with label and value
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        lbl = Gtk.Label(label=label)
        lbl.set_halign(Gtk.Align.START)
        lbl.add_css_class('section-title')
        header.append(lbl)
        
        header.append(Gtk.Box(hexpand=True))  # Spacer
        
        value_label = Gtk.Label(label=str(int(default)))
        value_label.add_css_class('dim-label')
        header.append(value_label)
        
        box.append(header)
        
        # Slider
        adjustment = Gtk.Adjustment(
            value=default,
            lower=min_val,
            upper=max_val,
            step_increment=1,
            page_increment=10
        )
        
        scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        scale.set_draw_value(False)
        scale.set_hexpand(True)
        
        # Store references for updating
        scale._value_label = value_label
        scale._callback = callback
        
        scale.connect('value-changed', self._on_slider_changed)
        
        box.append(scale)
        
        # Store reference by label
        attr_name = f'_scale_{label.lower()}'
        setattr(self, attr_name, scale)
        
        return box
        
    def _create_inset_section(self) -> Gtk.Box:
        """Create inset section."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Simple header
        lbl = Gtk.Label(label="Inset")
        lbl.set_halign(Gtk.Align.START)
        lbl.add_css_class('section-title')
        box.append(lbl)
        
        # Slider (strength when balance on, manual px when off)
        adjustment = Gtk.Adjustment(
            value=65,
            lower=0,
            upper=100,
            step_increment=1,
            page_increment=10
        )
        
        self._inset_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        self._inset_scale.set_draw_value(False)
        self._inset_scale.set_hexpand(True)
        self._inset_scale.connect('value-changed', self._on_inset_changed)
        
        box.append(self._inset_scale)
        
        return box
        
    def _on_slider_changed(self, scale: Gtk.Scale) -> None:
        """Generic slider change handler."""
        value = int(scale.get_value())
        if hasattr(scale, '_value_label'):
            scale._value_label.set_text(str(value))
        if hasattr(scale, '_callback'):
            scale._callback(value)
            
    def _on_padding_changed(self, value: int) -> None:
        """Handle padding change."""
        if self._updating:
            return
        self._state.padding_px = value
        self.emit('state-changed')
        
    def _on_radius_changed(self, value: int) -> None:
        """Handle radius change."""
        if self._updating:
            return
        self._state.radius_px = value
        self.emit('state-changed')
        
    def _on_shadow_changed(self, value: int) -> None:
        """Handle shadow change."""
        if self._updating:
            return
        self._state.shadow.strength = value / 100.0
        self.emit('state-changed')
        
    def _on_balance_toggled(self, switch, pspec) -> None:
        """Handle balance toggle."""
        if self._updating:
            return
        if switch.get_active():
            self._state.inset.mode = 'balance'
        else:
            self._state.inset.mode = 'manual'
        self.emit('state-changed')
        
    def _on_inset_changed(self, scale: Gtk.Scale) -> None:
        """Handle inset slider change."""
        if self._updating:
            return
        value = int(scale.get_value())
        
        if self._state.inset.mode == 'balance':
            self._state.inset.strength = value / 100.0
        else:
            self._state.inset.manual_px = value
            
        self.emit('state-changed')
        
    def _on_background_changed(self, bg_type: str, preset_id: str, image_path: Optional[str]) -> None:
        """Handle background change."""
        if self._updating:
            return
        self._state.background.type = bg_type
        self._state.background.preset_id = preset_id
        self._state.background.image_path = image_path
        self.emit('state-changed')
        
    def _on_output_changed(self, mode: str, ratio: tuple, size_px: tuple, platform: Optional[str]) -> None:
        """Handle output size/ratio change."""
        if self._updating:
            return
        self._state.output.mode = mode
        self._state.output.ratio = ratio
        self._state.output.size_px = size_px
        self._state.output.platform = platform
        self.emit('state-changed')
        
    def _on_preset_selected(self, dropdown, pspec) -> None:
        """Handle preset selection."""
        if self._updating:
            return
            
        idx = dropdown.get_selected()
        if 0 <= idx < len(self._preset_ids):
            preset_id = self._preset_ids[idx]
            preset = self._preset_manager.get(preset_id)
            if preset:
                self.set_state(preset.composition)
                # Update button states
                is_default = preset_id == self._config.get_default_preset()
                self._default_btn.set_icon_name('starred-symbolic' if is_default else 'emblem-favorite-symbolic')
                self._default_btn.set_sensitive(True)
                
                # Can't delete default preset or currently active default
                is_builtin = preset_id == 'default'
                self._delete_btn.set_sensitive(not is_builtin)
                
    def _on_set_default(self, button: Gtk.Button) -> None:
        """Set current preset as default."""
        idx = self._preset_dropdown.get_selected()
        if 0 <= idx < len(self._preset_ids):
            preset_id = self._preset_ids[idx]
            self._config.set_default_preset(preset_id)
            self._default_btn.set_icon_name('starred-symbolic')
            
    def _on_delete_preset(self, button: Gtk.Button) -> None:
        """Delete current preset."""
        idx = self._preset_dropdown.get_selected()
        if 0 <= idx < len(self._preset_ids):
            preset_id = self._preset_ids[idx]
            
            # Confirm dialog could be added here, but for now simple delete
            if self._preset_manager.delete_preset(preset_id):
                # If deleted the default, unset it
                if self._config.get_default_preset() == preset_id:
                    self._config.set_default_preset(None)
                    
                self._refresh_preset_list()
                
                # Select first item
                if self._preset_ids:
                    self._preset_dropdown.set_selected(0)
                
    def _on_save_preset(self, button: Gtk.Button) -> None:
        """Handle save preset button."""
        # Show dialog to get preset name
        dialog = Adw.MessageDialog(
            transient_for=self.get_root(),
            heading="Save Preset",
            body="Enter a name for this preset:"
        )
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("Preset name")
        dialog.set_extra_child(entry)
        
        dialog.add_response('cancel', 'Cancel')
        dialog.add_response('save', 'Save')
        dialog.set_response_appearance('save', Adw.ResponseAppearance.SUGGESTED)
        
        dialog.connect('response', self._on_save_dialog_response, entry)
        dialog.present()
        
    def _on_save_dialog_response(self, dialog, response: str, entry: Gtk.Entry) -> None:
        """Handle save dialog response."""
        if response == 'save':
            name = entry.get_text().strip()
            if name:
                from ..models.preset import Preset, PRESET_VERSION
                
                # Create safe ID
                preset_id = name.lower().replace(' ', '_')
                
                preset = Preset(
                    name=name,
                    version=PRESET_VERSION,
                    composition=self._state
                )
                
                self._preset_manager.save_preset(preset_id, preset)
                self._refresh_preset_list()
                
                # Select the new preset
                if preset_id in self._preset_ids:
                    idx = self._preset_ids.index(preset_id)
                    self._preset_dropdown.set_selected(idx)
                    
    def get_state(self) -> CompositionState:
        """Get the current composition state."""
        return self._state
        
    def set_state(self, state: CompositionState) -> None:
        """Set the composition state and update UI."""
        self._updating = True
        self._state = state
        
        # Update sliders
        if hasattr(self, '_scale_padding'):
            self._scale_padding.set_value(state.padding_px)
        if hasattr(self, '_scale_radius'):
            self._scale_radius.set_value(state.radius_px)
        if hasattr(self, '_scale_shadow'):
            self._scale_shadow.set_value(state.shadow.strength * 100)
            
        # Update inset (use strength as default)
        self._inset_scale.set_value(state.inset.strength * 100)
            
        # Update background
        if state.background.type == 'preset':
            self._background_picker.set_preset(state.background.preset_id)
            
        # Update ratio
        self._ratio_picker.set_mode(state.output.mode)
        
        self._updating = False
        self.emit('state-changed')
