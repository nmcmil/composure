"""Main application window."""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from typing import Optional
from PIL import Image
import tempfile
import os

from .widgets.canvas import ComposureCanvas
from .widgets.controls import ControlPanel
from .composer.pipeline import CompositionPipeline
from .capture.manager import CaptureManager


class ComposureWindow(Adw.ApplicationWindow):
    """Main application window for Composure."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.set_title("Composure")
        self.set_default_size(1100, 700)
        
        # Core components
        self._pipeline = CompositionPipeline()
        self._capture_manager = CaptureManager()
        self._render_timeout_id: Optional[int] = None
        
        # Build UI
        self._build_ui()
        
        # Connect signals
        self._connect_signals()
        
    def _build_ui(self):
        """Build the window UI."""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Headerbar
        header = Adw.HeaderBar()
        
        # Right side: Open, Copy, Save, Menu
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        open_btn = Gtk.Button(icon_name='document-open-symbolic')
        open_btn.set_tooltip_text("Open image (Ctrl+O)")
        open_btn.set_action_name('app.open')
        right_box.append(open_btn)
        
        copy_btn = Gtk.Button(icon_name='edit-copy-symbolic')
        copy_btn.set_tooltip_text("Copy to clipboard (Ctrl+C)")
        copy_btn.set_action_name('app.copy')
        right_box.append(copy_btn)
        
        save_btn = Gtk.Button(label="Save")
        save_btn.set_tooltip_text("Save image (Ctrl+S)")
        save_btn.set_action_name('app.save')
        right_box.append(save_btn)
        
        # Hamburger menu
        menu = Gio.Menu()
        menu.append("About Composure", "app.about")
        
        menu_btn = Gtk.MenuButton()
        menu_btn.set_icon_name("open-menu-symbolic")
        menu_btn.set_menu_model(menu)
        right_box.append(menu_btn)
        
        header.pack_end(right_box)
        
        main_box.append(header)
        
        # Content area: Canvas + Controls
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_box.set_vexpand(True)
        
        # Canvas (left side, expandable)
        canvas_frame = Gtk.Frame()
        canvas_frame.set_hexpand(True)
        canvas_frame.set_margin_start(12)
        canvas_frame.set_margin_end(6)
        canvas_frame.set_margin_top(12)
        canvas_frame.set_margin_bottom(12)
        canvas_frame.add_css_class('view')
        
        self._canvas = ComposureCanvas()
        canvas_frame.set_child(self._canvas)
        content_box.append(canvas_frame)
        
        # Controls (right side, fixed width)
        controls_frame = Gtk.Frame()
        controls_frame.set_margin_start(6)
        controls_frame.set_margin_end(12)
        controls_frame.set_margin_top(12)
        controls_frame.set_margin_bottom(12)
        controls_frame.add_css_class('view')
        
        self._controls = ControlPanel()
        controls_frame.set_child(self._controls)
        content_box.append(controls_frame)
        
        main_box.append(content_box)
        
        # Bottom bar with info
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom_bar.set_margin_start(12)
        bottom_bar.set_margin_end(12)
        bottom_bar.set_margin_bottom(8)
        
        self._info_label = Gtk.Label(label="Ready")
        self._info_label.add_css_class('dim-label')
        self._info_label.set_halign(Gtk.Align.START)
        bottom_bar.append(self._info_label)
        
        bottom_bar.append(Gtk.Box(hexpand=True))  # Spacer
        
        self._size_label = Gtk.Label(label="")
        self._size_label.add_css_class('dim-label')
        bottom_bar.append(self._size_label)
        
        main_box.append(bottom_bar)
        
        self.set_content(main_box)
        
    def _connect_signals(self):
        """Connect widget signals."""
        self._controls.connect('state-changed', self._on_state_changed)
        
    def _on_state_changed(self, controls):
        """Handle composition state changes."""
        # Update pipeline state
        self._pipeline.set_state(controls.get_state())
        self._pipeline.invalidate_cache()
        
        # Debounce render updates
        if self._render_timeout_id:
            GLib.source_remove(self._render_timeout_id)
            
        self._render_timeout_id = GLib.timeout_add(50, self._do_render)
        
    def _do_render(self) -> bool:
        """Perform the render and update canvas."""
        self._render_timeout_id = None
        
        result = self._pipeline.render()
        if result:
            self._canvas.set_image(result)
            
            # Update size label
            w, h = result.size
            self._size_label.set_text(f"{w} × {h}")
            
        return False  # Don't repeat
        
    def start_capture(self):
        """Start interactive screenshot capture."""
        self._info_label.set_text("Capturing... (use portal to select region)")
        
        # Don't hide the window - let the portal handle it
        # The portal will show its own overlay
        self._capture_manager.capture_interactive(self._on_capture_complete)
        
    def _on_capture_complete(self, result):
        """Handle capture completion."""
        if result:
            self._pipeline.set_image(result.image)
            self._pipeline.set_state(self._controls.get_state())
            self._do_render()
            self._info_label.set_text("Captured")
        else:
            self._info_label.set_text("Capture cancelled or failed")
            
    def open_file_dialog(self):
        """Show file open dialog."""
        self._info_label.set_text("Opening file dialog...")
        
        dialog = Gtk.FileDialog()
        dialog.set_title("Open Image")
        
        # Set up filters
        filter_images = Gtk.FileFilter()
        filter_images.set_name("Images")
        filter_images.add_mime_type("image/png")
        filter_images.add_mime_type("image/jpeg")
        filter_images.add_mime_type("image/webp")
        filter_images.add_mime_type("image/bmp")
        filter_images.add_mime_type("image/gif")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_images)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_images)
        
        dialog.open(self, None, self._on_open_complete)
        
    def _on_open_complete(self, dialog, result):
        """Handle file open completion."""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self._info_label.set_text(f"Loading: {os.path.basename(path)}")
                self.load_image(path)
        except GLib.Error as e:
            # Check if user cancelled vs actual error
            if "dismiss" in str(e).lower() or "cancel" in str(e).lower():
                self._info_label.set_text("Open cancelled")
            else:
                self._info_label.set_text(f"Open failed: {e.message}")
                print(f"File dialog error: {e}")
        except Exception as e:
            self._info_label.set_text(f"Error: {str(e)}")
            print(f"Unexpected error: {e}")
            
    def load_image(self, path: str):
        """Load an image from path."""
        try:
            if self._pipeline.load_image(path):
                self._pipeline.set_state(self._controls.get_state())
                self._do_render()
                self._info_label.set_text(f"Opened: {os.path.basename(path)}")
            else:
                self._info_label.set_text("Failed to load image")
        except Exception as e:
            self._info_label.set_text(f"Load error: {str(e)}")
            print(f"Load image error: {e}")
            
    def copy_to_clipboard(self):
        """Copy the composed image to clipboard using wl-copy for Wayland."""
        result = self._pipeline.render()
        if result is None:
            self._info_label.set_text("Nothing to copy")
            return
            
        try:
            import subprocess
            import threading
            
            # Get PNG bytes
            png_bytes = self._pipeline.export_bytes()
            if not png_bytes:
                self._info_label.set_text("Failed to export image")
                return
            
            def run_wl_copy():
                """Run wl-copy in background thread."""
                try:
                    process = subprocess.Popen(
                        ['wl-copy', '--type', 'image/png'],
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True  # Detach from main process
                    )
                    process.stdin.write(png_bytes)
                    process.stdin.close()
                    # Don't wait - let it run in background
                except Exception as e:
                    print(f"wl-copy thread error: {e}")
            
            # Start wl-copy in background thread
            thread = threading.Thread(target=run_wl_copy, daemon=True)
            thread.start()
            
            self._info_label.set_text("Copied to clipboard")
                
        except FileNotFoundError:
            self._info_label.set_text("Install wl-clipboard: sudo apt install wl-clipboard")
        except Exception as e:
            print(f"Clipboard error: {e}")
            self._info_label.set_text(f"Copy failed: {str(e)[:30]}")
            
    def save_image(self):
        """Save the composed image."""
        result = self._pipeline.render()
        if result is None:
            self._info_label.set_text("Nothing to save")
            return
            
        dialog = Gtk.FileDialog()
        dialog.set_title("Save Image")
        dialog.set_initial_name("composure_export.png")
        
        # Set up filters
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG Images")
        filter_png.add_mime_type("image/png")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_png)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_png)
        
        dialog.save(self, None, self._on_save_complete)
        
    def _on_save_complete(self, dialog, result):
        """Handle save completion."""
        try:
            file = dialog.save_finish(result)
            if file:
                path = file.get_path()
                if self._pipeline.export_png(path):
                    self._info_label.set_text(f"Saved: {os.path.basename(path)}")
                else:
                    self._info_label.set_text("Failed to save")
        except GLib.Error as e:
            if "dismiss" in str(e).lower() or "cancel" in str(e).lower():
                self._info_label.set_text("Save cancelled")
            else:
                self._info_label.set_text(f"Save failed: {e.message}")
        except Exception as e:
            self._info_label.set_text(f"Error: {str(e)}")
