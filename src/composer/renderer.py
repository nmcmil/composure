"""Rendering engine for composition output."""

import cairo
import math
from PIL import Image
from typing import Tuple, List, Optional
from dataclasses import dataclass
import io

from ..models.composition import (
    CompositionState,
    ShadowConfig,
    ShadowLayer,
    BACKGROUND_PRESETS,
)


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to RGB floats (0-1)."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def create_rounded_rect_path(ctx: cairo.Context, 
                              x: float, y: float, 
                              width: float, height: float, 
                              radius: float) -> None:
    """Create a rounded rectangle path."""
    if radius > min(width, height) / 2:
        radius = min(width, height) / 2
        
    # Top-left
    ctx.move_to(x + radius, y)
    # Top edge and top-right corner
    ctx.line_to(x + width - radius, y)
    ctx.arc(x + width - radius, y + radius, radius, -math.pi/2, 0)
    # Right edge and bottom-right corner
    ctx.line_to(x + width, y + height - radius)
    ctx.arc(x + width - radius, y + height - radius, radius, 0, math.pi/2)
    # Bottom edge and bottom-left corner
    ctx.line_to(x + radius, y + height)
    ctx.arc(x + radius, y + height - radius, radius, math.pi/2, math.pi)
    # Left edge and back to start
    ctx.line_to(x, y + radius)
    ctx.arc(x + radius, y + radius, radius, math.pi, 3*math.pi/2)
    ctx.close_path()


def render_gradient_background(ctx: cairo.Context,
                                width: int, height: int,
                                preset_id: str) -> None:
    """Render a gradient background from preset."""
    preset = BACKGROUND_PRESETS.get(preset_id, BACKGROUND_PRESETS['sky'])
    colors = [hex_to_rgb(c) for c in preset['colors']]
    
    if preset['type'] == 'solid':
        ctx.set_source_rgb(*colors[0])
        ctx.paint()
        
    elif preset['type'] == 'linear':
        angle = math.radians(preset.get('angle', 135))
        
        # Calculate gradient line based on angle
        cx, cy = width / 2, height / 2
        length = math.sqrt(width**2 + height**2)
        
        dx = math.cos(angle) * length / 2
        dy = math.sin(angle) * length / 2
        
        x0, y0 = cx - dx, cy - dy
        x1, y1 = cx + dx, cy + dy
        
        pattern = cairo.LinearGradient(x0, y0, x1, y1)
        pattern.add_color_stop_rgb(0, *colors[0])
        pattern.add_color_stop_rgb(1, *colors[1] if len(colors) > 1 else colors[0])
        
        ctx.set_source(pattern)
        ctx.paint()
        
    elif preset['type'] == 'radial':
        # Center radial gradient
        cx, cy = width / 2, height / 2
        radius = max(width, height) * 0.7
        
        pattern = cairo.RadialGradient(cx, cy, 0, cx, cy, radius)
        pattern.add_color_stop_rgb(0, *colors[0])
        pattern.add_color_stop_rgb(1, *colors[1] if len(colors) > 1 else colors[0])
        
        ctx.set_source(pattern)
        ctx.paint()


def render_image_background(ctx: cairo.Context,
                            width: int, height: int,
                            image_path: str) -> None:
    """Render an image as background (cover fill)."""
    try:
        bg_image = Image.open(image_path).convert('RGBA')
        bg_w, bg_h = bg_image.size
        
        # Cover fill: scale to fill entire canvas
        scale = max(width / bg_w, height / bg_h)
        new_w = int(bg_w * scale)
        new_h = int(bg_h * scale)
        
        bg_resized = bg_image.resize((new_w, new_h), Image.LANCZOS)
        
        # Center crop
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        bg_cropped = bg_resized.crop((left, top, left + width, top + height))
        
        # Convert to cairo surface
        surface, _data = pil_to_cairo_surface(bg_cropped)
        ctx.set_source_surface(surface, 0, 0)
        ctx.paint()
        
    except Exception as e:
        print(f"Failed to load background image: {e}")
        # Fallback to solid gray
        ctx.set_source_rgb(0.2, 0.2, 0.22)
        ctx.paint()


def pil_to_cairo_surface(image: Image.Image) -> tuple:
    """
    Convert PIL Image to Cairo ImageSurface.
    
    Returns a tuple of (surface, data_ref) where data_ref must be kept
    alive for the surface to remain valid.
    """
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
        
    # Cairo expects BGRA (on little-endian)
    data = bytearray(image.tobytes('raw', 'BGRa'))
    
    surface = cairo.ImageSurface.create_for_data(
        data,
        cairo.FORMAT_ARGB32,
        image.width,
        image.height,
        image.width * 4
    )
    
    # Return both surface and data reference to prevent GC
    return (surface, data)


def cairo_surface_to_pil(surface: cairo.ImageSurface) -> Image.Image:
    """Convert Cairo ImageSurface to PIL Image."""
    buf = surface.get_data()
    width = surface.get_width()
    height = surface.get_height()
    
    # Cairo ARGB32 is BGRA on little-endian
    image = Image.frombuffer(
        'RGBA',
        (width, height),
        bytes(buf),
        'raw',
        'BGRa',
        surface.get_stride(),
        1
    )
    
    return image.copy()  # Copy to detach from buffer


def render_shadow(ctx: cairo.Context,
                  x: float, y: float,
                  width: float, height: float,
                  radius: float,
                  shadow: ShadowConfig) -> None:
    from PIL import ImageFilter, ImageDraw
    
    if shadow.strength <= 0:
        return
        
    for layer in shadow.layers:
        # Dynamic scaling based on strength
        # Opacity: Linear scaling
        opacity = layer.opacity * shadow.strength
        
        # Dimensions: Scale with strength to make shadow "grow"
        # range: 0.8x to 1.4x of base value
        scale_factor = 0.8 + (shadow.strength * 0.6)
        
        current_blur = layer.blur * scale_factor
        current_offset_y = layer.offset_y * scale_factor
        current_spread = layer.spread * scale_factor
        
        if opacity <= 0.01:
            continue
            
        # 1. Create a mask image for the shadow shape
        blur_radius = current_blur
        padding = int(blur_radius * 2)
        
        # Dimensions of the shadow mask
        mask_w = int(width + padding * 2)
        mask_h = int(height + padding * 2)
        
        # Create mask: transparent background, black shape
        mask = Image.new('RGBA', (mask_w, mask_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask)
        
        # Draw the rounded rect in black
        # Position centered in the padded mask
        shape_x = padding
        shape_y = padding
        
        draw.rounded_rectangle(
            (shape_x, shape_y, shape_x + width, shape_y + height),
            radius=radius,
            fill=(0, 0, 0, 255)
        )
        
        # 2. Apply Gaussian Blur
        blurred_mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius / 2))
        
        # 3. Apply Opacity
        if opacity < 1.0:
            r, g, b, a = blurred_mask.split()
            a = a.point(lambda p: int(p * opacity))
            blurred_mask = Image.merge('RGBA', (r, g, b, a))
        
        # 4. Draw to Cairo Context
        dest_x = x + current_spread - padding
        dest_y = y + current_spread + current_offset_y - padding
        
        # Adjust size for spread (spread expands/contracts the shape)
        if current_spread != 0:
            # Re-scaling might be needed for perfect spread correctness, 
            # but simpler approximation is often enough. 
            # For exact "spread" like CSS, we should resize the initial rect.
            # AND WE DID: We drew the rect with 'width' and 'height'.
            # Correct logic:
            # If spread is positive, the source shape should be larger.
            # If spread is negative, the source shape should be smaller.
            # Rerunning logic: 
            # We want the shadow CAST by a rect of (width + 2*spread, height + 2*spread)
            
            # Recalculate mask for spread support
            spread_w = width + current_spread * 2
            spread_h = height + current_spread * 2
            
            if spread_w <= 0 or spread_h <= 0:
                continue
                
            mask = Image.new('RGBA', (mask_w, mask_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(mask)
            
            # Recalculate centered position
            center_x = mask_w / 2
            center_y = mask_h / 2
            
            draw.rounded_rectangle(
                (center_x - spread_w/2, center_y - spread_h/2, 
                 center_x + spread_w/2, center_y + spread_h/2),
                radius=max(0, radius + current_spread),
                fill=(0, 0, 0, 255)
            )
            # Apply Gaussian Blur
            blurred_mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius / 2))
            
            # Apply Opacity
            if opacity < 1.0:
                r, g, b, a = blurred_mask.split()
                a = a.point(lambda p: int(p * opacity))
                blurred_mask = Image.merge('RGBA', (r, g, b, a))

        # Convert to cairo and draw
        shadow_surface, _data = pil_to_cairo_surface(blurred_mask)
        ctx.set_source_surface(shadow_surface, dest_x, dest_y)
        ctx.paint()


def render_card(ctx: cairo.Context,
                card_image: Image.Image,
                x: float, y: float,
                width: float, height: float,
                radius: float) -> None:
    """Render the screenshot card with rounded corners."""
    # Scale card image to target size
    card_resized = card_image.resize((int(width), int(height)), Image.LANCZOS)
    
    # Convert to cairo surface (keep _data ref to prevent GC)
    card_surface, _data = pil_to_cairo_surface(card_resized)
    
    ctx.save()
    
    # Clip to rounded rect
    create_rounded_rect_path(ctx, x, y, width, height, radius)
    ctx.clip()
    
    # Draw the card image
    ctx.set_source_surface(card_surface, x, y)
    ctx.paint()
    
    ctx.restore()


class CompositionRenderer:
    """Renders a complete composition from state and input image."""
    
    def __init__(self, input_image: Image.Image, state: CompositionState):
        self.input_image = input_image
        self.state = state
        
    def compute_output_size(self) -> Tuple[int, int]:
        """Determine the output canvas size based on state."""
        mode = self.state.output.mode
        
        if mode == 'fixedSize':
            return self.state.output.size_px
            
        elif mode == 'platform':
            from ..models.composition import PLATFORM_PRESETS
            platform = self.state.output.platform
            if platform and platform in PLATFORM_PRESETS:
                preset = PLATFORM_PRESETS[platform]
                return (preset['width'], preset['height'])
            return self.state.output.size_px
            
        elif mode == 'fixedRatio':
            ratio_w, ratio_h = self.state.output.ratio
            # Use input dimensions as base, adjust to match ratio
            in_w, in_h = self.input_image.size
            
            # Target: maintain similar area but with target ratio
            target_ratio = ratio_w / ratio_h
            current_ratio = in_w / in_h
            
            if current_ratio > target_ratio:
                # Input is wider, keep width
                out_w = in_w + self.state.padding_px * 2
                out_h = int(out_w / target_ratio)
            else:
                # Input is taller, keep height  
                out_h = in_h + self.state.padding_px * 2
                out_w = int(out_h * target_ratio)
                
            return (out_w, out_h)
            
        else:  # autoRatio
            in_w, in_h = self.input_image.size
            return (
                in_w + self.state.padding_px * 2,
                in_h + self.state.padding_px * 2
            )
            
    def render(self) -> Image.Image:
        """Render the complete composition."""
        from .balance import compute_balanced_insets, compute_manual_insets, apply_insets
        
        # Step 1: Compute insets and crop
        inset_config = self.state.inset
        if inset_config.mode == 'balance':
            insets = compute_balanced_insets(
                self.input_image,
                strength=inset_config.strength
            )
            # Store computed insets back
            inset_config.balanced_insets_px = insets.as_dict()
        else:
            insets = compute_manual_insets(inset_config.manual_px)
            
        card_image = apply_insets(self.input_image, insets)
        card_w, card_h = card_image.size
        
        # Step 2: Compute output size
        out_w, out_h = self.compute_output_size()
        
        # Step 3: Calculate card placement FIRST to know if we need transparent margins
        padding = self.state.padding_px
        
        # Calculate required margin for shadow (based on actual shadow config)
        # Shadow extends differently on each side - bottom needs extra for offset_y
        shadow_margin_base = 0  # For top, left, right
        shadow_margin_bottom = 0  # Extra for bottom due to offset_y
        if self.state.shadow.strength > 0:
            for layer in self.state.shadow.layers:
                # Base margin: blur extends outward, spread can expand or contract
                base = (layer.blur / 2) + max(0, -layer.spread)  # -spread means expansion
                shadow_margin_base = max(shadow_margin_base, base)
                # Bottom margin: base + offset_y (shadow drops down)
                bottom = base + layer.offset_y
                shadow_margin_bottom = max(shadow_margin_bottom, bottom)
            shadow_margin_base = int(shadow_margin_base * self.state.shadow.strength) + 8
            shadow_margin_bottom = int(shadow_margin_bottom * self.state.shadow.strength) + 8
        
        # Use the larger of the two for uniform padding (simplest approach)
        shadow_margin = max(shadow_margin_base, shadow_margin_bottom)
        
        # Effective padding is always at least the shadow margin
        effective_padding = max(padding, shadow_margin)
        
        # Update output size to ensure shadow fits
        if effective_padding > padding:
            out_w = card_w + effective_padding * 2
            out_h = card_h + effective_padding * 2
        
        # Step 4: Create cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, out_w, out_h)
        ctx = cairo.Context(surface)
        
        # Step 5: Render background
        bg = self.state.background
        if bg.type == 'preset':
            render_gradient_background(ctx, out_w, out_h, bg.preset_id)
        elif bg.type == 'image' and bg.image_path:
            render_image_background(ctx, out_w, out_h, bg.image_path)
        else:
            render_gradient_background(ctx, out_w, out_h, 'sky')
            
        # Step 6: Calculate available space for card
        available_w = out_w - effective_padding * 2
        available_h = out_h - effective_padding * 2
        
        # Scale card to fit within available space (contain)
        scale = min(available_w / card_w, available_h / card_h)
        draw_w = card_w * scale
        draw_h = card_h * scale
        
        # Center the card
        draw_x = (out_w - draw_w) / 2
        draw_y = (out_h - draw_h) / 2
        
        # Step 7: Render shadow
        render_shadow(
            ctx, draw_x, draw_y, draw_w, draw_h,
            self.state.radius_px,
            self.state.shadow
        )
        
        # Step 8: Render card with rounded corners
        render_card(ctx, card_image, draw_x, draw_y, draw_w, draw_h, self.state.radius_px)
        
        # Convert to PIL Image
        return cairo_surface_to_pil(surface)
