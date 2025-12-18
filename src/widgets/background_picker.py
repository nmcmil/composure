"""Background picker widget."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, GLib
from typing import Callable, Optional
import cairo
import math

from ..models.composition import BACKGROUND_PRESETS


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB floats."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


class BackgroundPresetButton(Gtk.ToggleButton):
    """A button that shows a background preset preview."""
    
    def __init__(self, preset_id: str, preset: dict):
        super().__init__()
        
        self.preset_id = preset_id
        self.preset = preset
        
        self.set_size_request(48, 48)
        self.add_css_class('preset-button')
        self.add_css_class('flat')
        
        # Set tooltip
        self.set_tooltip_text(preset.get('name', preset_id))
        
        # Create drawing area for preview
        drawing = Gtk.DrawingArea()
        drawing.set_content_width(40)
        drawing.set_content_height(40)
        drawing.set_draw_func(self._on_draw)
        
        self.set_child(drawing)
        
    def _on_draw(self, area, ctx, width, height):
        """Draw the preset preview."""
        # Draw rounded rect clip
        radius = 6
        self._draw_rounded_rect(ctx, 0, 0, width, height, radius)
        ctx.clip()
        
        colors = [hex_to_rgb(c) for c in self.preset.get('colors', ['#888888'])]
        preset_type = self.preset.get('type', 'solid')
        
        if preset_type == 'solid':
            ctx.set_source_rgb(*colors[0])
            ctx.paint()
            
        elif preset_type == 'linear':
            angle = math.radians(self.preset.get('angle', 135))
            cx, cy = width / 2, height / 2
            length = math.sqrt(width**2 + height**2)
            dx = math.cos(angle) * length / 2
            dy = math.sin(angle) * length / 2
            
            pattern = cairo.LinearGradient(cx - dx, cy - dy, cx + dx, cy + dy)
            pattern.add_color_stop_rgb(0, *colors[0])
            if len(colors) > 1:
                pattern.add_color_stop_rgb(1, *colors[1])
            else:
                pattern.add_color_stop_rgb(1, *colors[0])
                
            ctx.set_source(pattern)
            ctx.paint()
            
        elif preset_type == 'radial':
            cx, cy = width / 2, height / 2
            radius_grad = max(width, height) * 0.7
            
            pattern = cairo.RadialGradient(cx, cy, 0, cx, cy, radius_grad)
            pattern.add_color_stop_rgb(0, *colors[0])
            if len(colors) > 1:
                pattern.add_color_stop_rgb(1, *colors[1])
            else:
                pattern.add_color_stop_rgb(1, *colors[0])
                
            ctx.set_source(pattern)
            ctx.paint()
            
        # Add subtle border for light colors (like white)
        colors = self.preset.get('colors', ['#888888'])
        first_color = hex_to_rgb(colors[0])
        # Check if color is light (simple luminance check)
        luminance = 0.299 * first_color[0] + 0.587 * first_color[1] + 0.114 * first_color[2]
        if luminance > 0.8:
            # Draw subtle border
            ctx.set_source_rgba(0, 0, 0, 0.15)
            self._draw_rounded_rect(ctx, 0.5, 0.5, width - 1, height - 1, radius)
            ctx.set_line_width(1)
            ctx.stroke()
            
    def _draw_rounded_rect(self, ctx, x, y, width, height, radius):
        """Draw rounded rectangle path."""
        ctx.new_path()
        ctx.move_to(x + radius, y)
        ctx.line_to(x + width - radius, y)
        ctx.arc(x + width - radius, y + radius, radius, -math.pi/2, 0)
        ctx.line_to(x + width, y + height - radius)
        ctx.arc(x + width - radius, y + height - radius, radius, 0, math.pi/2)
        ctx.line_to(x + radius, y + height)
        ctx.arc(x + radius, y + height - radius, radius, math.pi/2, math.pi)
        ctx.line_to(x, y + radius)
        ctx.arc(x + radius, y + radius, radius, math.pi, 3*math.pi/2)
        ctx.close_path()


class BackgroundPicker(Gtk.Box):
    """Widget for selecting background presets or custom images."""
    
    def __init__(self, on_change: Optional[Callable[[str, str, Optional[str]], None]] = None):
        """
        Args:
            on_change: Callback(type, preset_id, image_path)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        self._on_change = on_change
        self._current_preset: Optional[str] = 'slate'
        self._buttons: dict[str, BackgroundPresetButton] = {}
        
        # Section label
        label = Gtk.Label(label="Background")
        label.set_halign(Gtk.Align.START)
        label.add_css_class('section-title')
        self.append(label)
        
        # Organize presets by layer
        layer_1 = [(k, v) for k, v in BACKGROUND_PRESETS.items() if v.get('layer') == 1]
        layer_2 = [(k, v) for k, v in BACKGROUND_PRESETS.items() if v.get('layer') == 2]
        layer_3 = [(k, v) for k, v in BACKGROUND_PRESETS.items() if v.get('layer') == 3]
        
        # Layer 1: Flat Colors
        self._add_preset_row(layer_1)
        
        # Layer 2: Subtle Gradients
        self._add_preset_row(layer_2)
        
        # Layer 3: Loud Gradients
        self._add_preset_row(layer_3)
        
        # Custom button only (Desktop removed)
        extras_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        extras_box.set_margin_top(4)
        
        custom_btn = Gtk.Button(label="Custom…")
        custom_btn.add_css_class('flat')
        custom_btn.connect('clicked', self._on_custom_clicked)
        extras_box.append(custom_btn)
        
        self.append(extras_box)
        
        # Set initial selection
        self.set_preset('slate')
        
    def _add_preset_row(self, presets: list) -> None:
        """Add a row of preset buttons."""
        grid = Gtk.FlowBox()
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_max_children_per_line(8)
        grid.set_min_children_per_line(8)
        grid.set_row_spacing(4)
        grid.set_column_spacing(4)
        
        for preset_id, preset in presets:
            button = BackgroundPresetButton(preset_id, preset)
            button.connect('toggled', self._on_preset_toggled)
            self._buttons[preset_id] = button
            grid.append(button)
            
        self.append(grid)
        
    def set_preset(self, preset_id: str) -> None:
        """Set the selected preset."""
        for pid, button in self._buttons.items():
            button.set_active(pid == preset_id)
        self._current_preset = preset_id
        
    def _on_preset_toggled(self, button: BackgroundPresetButton) -> None:
        """Handle preset button toggle."""
        if button.get_active():
            # Deselect others
            for pid, btn in self._buttons.items():
                if btn != button:
                    btn.set_active(False)
                    
            self._current_preset = button.preset_id
            
            if self._on_change:
                self._on_change('preset', button.preset_id, None)
                
    def _on_desktop_clicked(self, button: Gtk.Button) -> None:
        """Handle desktop wallpaper button."""
        from ..capture.portal import get_desktop_wallpaper
        
        wallpaper = get_desktop_wallpaper()
        if wallpaper:
            # Deselect preset buttons
            for btn in self._buttons.values():
                btn.set_active(False)
            self._current_preset = None
            
            if self._on_change:
                self._on_change('desktop', '', wallpaper)
        else:
            # Show toast or dialog that wallpaper couldn't be found
            pass
            
    def _on_custom_clicked(self, button: Gtk.Button) -> None:
        """Handle custom image button."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Background Image")
        
        # Set up filters
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Images")
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/webp")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_images)
        
        # Get window
        window = self.get_root()
        
        dialog.open(window, None, self._on_file_selected)
        
    def _on_file_selected(self, dialog, result) -> None:
        """Handle file selection."""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                
                # Deselect preset buttons
                for btn in self._buttons.values():
                    btn.set_active(False)
                self._current_preset = None
                
                if self._on_change:
                    self._on_change('image', '', path)
                    
        except GLib.Error:
            # User cancelled
            pass


# Import Gio for file dialog
from gi.repository import Gio
