"""Balance algorithm for automatic content-aware inset calculation."""

from PIL import Image
from typing import Tuple, Dict
from dataclasses import dataclass

from .detector import (
    detect_edge_background,
    detect_content_saliency,
    detect_window_transparency,
    EdgeTrims,
    ContentBounds,
)


@dataclass
class BalancedInsets:
    """Computed inset values for each edge."""
    left: int
    right: int
    top: int
    bottom: int
    
    def as_dict(self) -> Dict[str, int]:
        return {
            'l': self.left,
            'r': self.right,
            't': self.top,
            'b': self.bottom
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'BalancedInsets':
        return cls(
            left=data.get('l', 0),
            right=data.get('r', 0),
            top=data.get('t', 0),
            bottom=data.get('b', 0)
        )


def compute_balanced_insets(
    image: Image.Image,
    strength: float = 1.0,
    is_window_capture: bool = False,
    margin: int = 16,
    upward_bias: float = 0.05
) -> BalancedInsets:
    """
    Compute balanced insets for aesthetically centered content.
    
    Combines edge-based background detection with saliency-based
    content detection to produce asymmetric insets that center
    the content visually.
    
    Args:
        image: PIL Image to analyze
        strength: Inset strength (0 = no inset, 1 = full computed inset)
        is_window_capture: Whether this is a window capture (enables transparency detection)
        margin: Minimum margin to keep around content
        upward_bias: Slight upward bias for aesthetic centering (0-1)
        
    Returns:
        BalancedInsets with per-edge trim values
    """
    w, h = image.size
    
    # Step 1: Detect background margins
    edge_trims = detect_edge_background(image)
    
    # Step 1b: For window captures, also check transparency
    if is_window_capture and image.mode == 'RGBA':
        transparency_trims = detect_window_transparency(image)
        # Take the maximum of both detectors
        edge_trims = EdgeTrims(
            left=max(edge_trims.left, transparency_trims.left),
            right=max(edge_trims.right, transparency_trims.right),
            top=max(edge_trims.top, transparency_trims.top),
            bottom=max(edge_trims.bottom, transparency_trims.bottom)
        )
    
    # Step 2: Detect content bounds
    content_bounds = detect_content_saliency(image)
    
    if content_bounds is None:
        # Fallback: use only edge detection
        content_bounds = ContentBounds(
            left=edge_trims.left,
            top=edge_trims.top,
            right=w - edge_trims.right,
            bottom=h - edge_trims.bottom
        )
    
    # Step 3: Ensure edge trims don't cut into content + margin
    safe_left = max(0, content_bounds.left - margin)
    safe_right = max(0, w - content_bounds.right - margin)
    safe_top = max(0, content_bounds.top - margin)
    safe_bottom = max(0, h - content_bounds.bottom - margin)
    
    # Clamp edge trims to safe values
    left_trim = min(edge_trims.left, safe_left)
    right_trim = min(edge_trims.right, safe_right)
    top_trim = min(edge_trims.top, safe_top)
    bottom_trim = min(edge_trims.bottom, safe_bottom)
    
    # Step 4: Aesthetic centering
    # Compute content centroid in input space
    cx, cy = content_bounds.center
    
    # Target center (with upward bias)
    tx = w / 2
    ty = h / 2 * (1 - upward_bias)
    
    # Compute how much content is offset from target
    offset_x = cx - tx
    offset_y = cy - ty
    
    # Adjust trims to center content
    # If content is right of center (positive offset_x), trim more from right
    if offset_x > 0:
        extra_right = min(int(offset_x * 0.5), safe_right - right_trim)
        right_trim += max(0, extra_right)
    else:
        extra_left = min(int(-offset_x * 0.5), safe_left - left_trim)
        left_trim += max(0, extra_left)
    
    # If content is below center (positive offset_y), trim more from bottom
    if offset_y > 0:
        extra_bottom = min(int(offset_y * 0.5), safe_bottom - bottom_trim)
        bottom_trim += max(0, extra_bottom)
    else:
        extra_top = min(int(-offset_y * 0.5), safe_top - top_trim)
        top_trim += max(0, extra_top)
    
    # Step 5: Apply strength
    left_final = int(left_trim * strength)
    right_final = int(right_trim * strength)
    top_final = int(top_trim * strength)
    bottom_final = int(bottom_trim * strength)
    
    return BalancedInsets(
        left=left_final,
        right=right_final,
        top=top_final,
        bottom=bottom_final
    )


def compute_manual_insets(inset_px: int) -> BalancedInsets:
    """
    Compute uniform manual insets.
    
    Args:
        inset_px: Uniform inset in pixels for all edges
        
    Returns:
        BalancedInsets with equal values on all edges
    """
    return BalancedInsets(
        left=inset_px,
        right=inset_px,
        top=inset_px,
        bottom=inset_px
    )


def apply_insets(image: Image.Image, insets: BalancedInsets) -> Image.Image:
    """
    Apply insets to crop an image.
    
    Ensures insets never exceed image dimensions - always leaves at least
    10% of the original image in each dimension.
    
    Args:
        image: Source image
        insets: Inset values for each edge
        
    Returns:
        Cropped image
    """
    w, h = image.size
    
    # Minimum size to keep (at least 10% of original)
    min_w = max(50, w // 10)
    min_h = max(50, h // 10)
    
    # Maximum total horizontal inset
    max_horizontal = w - min_w
    # Maximum total vertical inset
    max_vertical = h - min_h
    
    # Get requested insets, clamped to non-negative
    left = max(0, insets.left)
    right = max(0, insets.right)
    top = max(0, insets.top)
    bottom = max(0, insets.bottom)
    
    # Scale down proportionally if combined insets exceed max
    total_h = left + right
    if total_h > max_horizontal:
        scale = max_horizontal / total_h
        left = int(left * scale)
        right = int(right * scale)
    
    total_v = top + bottom
    if total_v > max_vertical:
        scale = max_vertical / total_v
        top = int(top * scale)
        bottom = int(bottom * scale)
    
    # Ensure we have valid crop box
    crop_left = left
    crop_top = top
    crop_right = max(crop_left + min_w, w - right)
    crop_bottom = max(crop_top + min_h, h - bottom)
    
    crop_box = (crop_left, crop_top, crop_right, crop_bottom)
    
    return image.crop(crop_box)
