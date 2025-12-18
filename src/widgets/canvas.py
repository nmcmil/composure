"""Canvas widget for composition preview."""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from PIL import Image
import cairo
from typing import Optional
import io


class ComposureCanvas(Gtk.DrawingArea):
    """
    Drawing area that displays the composition preview.
    
    Renders the composed image with proper scaling to fit the widget.
    """
    
    def __init__(self):
        super().__init__()
        
        self._image: Optional[Image.Image] = None
        self._pixbuf: Optional[GdkPixbuf.Pixbuf] = None
        
        # Enable drawing
        self.set_draw_func(self._on_draw)
        
        # Set size hints
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_size_request(400, 300)
        
        # Add CSS class
        self.add_css_class('canvas-container')
        
    def set_image(self, image: Optional[Image.Image]) -> None:
        """
        Set the image to display.
        
        Args:
            image: PIL Image to display, or None to clear
        """
        self._image = image
        self._pixbuf = None
        
        if image is not None:
            self._pixbuf = self._pil_to_pixbuf(image)
            
        # Request redraw
        self.queue_draw()
        
    def _pil_to_pixbuf(self, image: Image.Image) -> GdkPixbuf.Pixbuf:
        """Convert PIL Image to GdkPixbuf."""
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        width, height = image.size
        data = image.tobytes()
        
        return GdkPixbuf.Pixbuf.new_from_data(
            data,
            GdkPixbuf.Colorspace.RGB,
            False,  # has_alpha
            8,      # bits_per_sample
            width,
            height,
            width * 3,  # rowstride
            None,   # destroy_fn
            None    # destroy_fn_data
        )
        
    def _on_draw(self, area, ctx, width, height):
        """Draw callback."""
        # Fill background with subtle pattern
        ctx.set_source_rgb(0.15, 0.15, 0.17)
        ctx.paint()
        
        # Draw checkerboard pattern (indicates transparency)
        self._draw_checkerboard(ctx, width, height)
        
        if self._pixbuf is None:
            # Draw placeholder
            self._draw_placeholder(ctx, width, height)
            return
            
        # Calculate scaling to fit while maintaining aspect ratio
        img_w = self._pixbuf.get_width()
        img_h = self._pixbuf.get_height()
        
        # Add padding
        padding = 24
        available_w = width - padding * 2
        available_h = height - padding * 2
        
        scale = min(available_w / img_w, available_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        
        # Center the image
        x = (width - draw_w) / 2
        y = (height - draw_h) / 2
        
        # Draw shadow behind preview
        ctx.set_source_rgba(0, 0, 0, 0.3)
        self._draw_rounded_rect(ctx, x + 4, y + 4, draw_w, draw_h, 8)
        ctx.fill()
        
        # Clip to rounded rect
        ctx.save()
        self._draw_rounded_rect(ctx, x, y, draw_w, draw_h, 8)
        ctx.clip()
        
        # Scale and draw image
        ctx.translate(x, y)
        ctx.scale(scale, scale)
        Gdk.cairo_set_source_pixbuf(ctx, self._pixbuf, 0, 0)
        ctx.paint()
        
        ctx.restore()
        
        # Draw border
        ctx.set_source_rgba(1, 1, 1, 0.1)
        ctx.set_line_width(1)
        self._draw_rounded_rect(ctx, x, y, draw_w, draw_h, 8)
        ctx.stroke()
        
    def _draw_checkerboard(self, ctx, width, height):
        """Draw a subtle checkerboard pattern."""
        cell_size = 16
        color1 = (0.12, 0.12, 0.14)
        color2 = (0.14, 0.14, 0.16)
        
        for y in range(0, int(height), cell_size):
            for x in range(0, int(width), cell_size):
                if (x // cell_size + y // cell_size) % 2 == 0:
                    ctx.set_source_rgb(*color1)
                else:
                    ctx.set_source_rgb(*color2)
                ctx.rectangle(x, y, cell_size, cell_size)
                ctx.fill()
                
    def _draw_placeholder(self, ctx, width, height):
        """Draw a placeholder when no image is loaded."""
        # Just draw simple text
        ctx.set_source_rgba(1, 1, 1, 0.3)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(16)
        
        text = "Take a screenshot to get started"
        extents = ctx.text_extents(text)
        ctx.move_to((width - extents.width) / 2, height / 2)
        ctx.show_text(text)
        
    def _draw_rounded_rect(self, ctx, x, y, width, height, radius):
        """Draw a rounded rectangle path."""
        import math
        
        if radius > min(width, height) / 2:
            radius = min(width, height) / 2
            
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
