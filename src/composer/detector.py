"""Content detection for automatic balance and inset calculation.

This module uses pure Python/PIL for image processing to avoid numpy dependency.
"""

from PIL import Image, ImageFilter
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class ContentBounds:
    """Bounding box for detected content."""
    left: int
    top: int
    right: int
    bottom: int
    
    @property
    def width(self) -> int:
        return self.right - self.left
    
    @property
    def height(self) -> int:
        return self.bottom - self.top
    
    @property
    def center(self) -> Tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)


@dataclass
class EdgeTrims:
    """Per-edge trim amounts in pixels."""
    left: int
    right: int
    top: int
    bottom: int


def get_pixel_variance(pixels: List[Tuple[int, int, int]]) -> float:
    """Calculate color variance for a list of RGB pixels."""
    if not pixels:
        return 0.0
        
    n = len(pixels)
    if n == 0:
        return 0.0
        
    # Calculate mean
    mean_r = sum(p[0] for p in pixels) / n
    mean_g = sum(p[1] for p in pixels) / n
    mean_b = sum(p[2] for p in pixels) / n
    
    # Calculate variance
    var_r = sum((p[0] - mean_r) ** 2 for p in pixels) / n
    var_g = sum((p[1] - mean_g) ** 2 for p in pixels) / n
    var_b = sum((p[2] - mean_b) ** 2 for p in pixels) / n
    
    return var_r + var_g + var_b


def detect_edge_background(image: Image.Image, 
                           band_percent: float = 0.04,
                           variance_threshold: float = 500.0) -> EdgeTrims:
    """
    Detect uniform background margins by analyzing edge bands.
    
    Sweeps inward from each edge until color variance increases
    above threshold, indicating content.
    
    Args:
        image: PIL Image to analyze
        band_percent: Percentage of image dimension for sampling band
        variance_threshold: Color variance threshold for content detection
        
    Returns:
        EdgeTrims with per-edge trim amounts
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    w, h = image.size
    band_h = max(2, int(h * band_percent))
    band_w = max(2, int(w * band_percent))
    
    # Sample step for performance
    sample_step = max(1, min(w, h) // 100)
    
    def get_row_pixels(y_start: int, y_end: int) -> List[Tuple[int, int, int]]:
        """Get sampled pixels from a horizontal band."""
        pixels = []
        for y in range(y_start, y_end):
            for x in range(0, w, sample_step):
                pixels.append(image.getpixel((x, y)))
        return pixels
    
    def get_col_pixels(x_start: int, x_end: int) -> List[Tuple[int, int, int]]:
        """Get sampled pixels from a vertical band."""
        pixels = []
        for x in range(x_start, x_end):
            for y in range(0, h, sample_step):
                pixels.append(image.getpixel((x, y)))
        return pixels
    
    # Limit max trim to 40% of dimension
    max_trim_h = int(h * 0.4)
    max_trim_w = int(w * 0.4)
    
    # Find top trim
    top_trim = 0
    for offset in range(0, max_trim_h, band_h):
        pixels = get_row_pixels(offset, min(offset + band_h, h))
        if get_pixel_variance(pixels) > variance_threshold:
            break
        top_trim = offset + band_h
    top_trim = min(top_trim, max_trim_h)
    
    # Find bottom trim
    bottom_trim = 0
    for offset in range(0, max_trim_h, band_h):
        y_start = max(0, h - offset - band_h)
        y_end = h - offset
        pixels = get_row_pixels(y_start, y_end)
        if get_pixel_variance(pixels) > variance_threshold:
            break
        bottom_trim = offset + band_h
    bottom_trim = min(bottom_trim, max_trim_h)
    
    # Find left trim
    left_trim = 0
    for offset in range(0, max_trim_w, band_w):
        pixels = get_col_pixels(offset, min(offset + band_w, w))
        if get_pixel_variance(pixels) > variance_threshold:
            break
        left_trim = offset + band_w
    left_trim = min(left_trim, max_trim_w)
    
    # Find right trim
    right_trim = 0
    for offset in range(0, max_trim_w, band_w):
        x_start = max(0, w - offset - band_w)
        x_end = w - offset
        pixels = get_col_pixels(x_start, x_end)
        if get_pixel_variance(pixels) > variance_threshold:
            break
        right_trim = offset + band_w
    right_trim = min(right_trim, max_trim_w)
    
    return EdgeTrims(
        left=left_trim,
        right=right_trim,
        top=top_trim,
        bottom=bottom_trim
    )


def detect_content_saliency(image: Image.Image,
                            edge_threshold: int = 30,
                            min_content_area: int = 100) -> Optional[ContentBounds]:
    """
    Detect content bounding box using edge detection.
    
    Computes edges and finds the bounding box of significant edge regions.
    
    Args:
        image: PIL Image to analyze
        edge_threshold: Threshold for edge detection
        min_content_area: Minimum pixels for valid content
        
    Returns:
        ContentBounds or None if no content detected
    """
    # Convert to grayscale and detect edges
    gray = image.convert('L')
    edges = gray.filter(ImageFilter.FIND_EDGES)
    
    w, h = edges.size
    
    # Find bounding box of edges above threshold
    min_x, min_y = w, h
    max_x, max_y = 0, 0
    edge_count = 0
    
    # Sample for performance
    sample_step = max(1, min(w, h) // 200)
    
    for y in range(0, h, sample_step):
        for x in range(0, w, sample_step):
            pixel = edges.getpixel((x, y))
            if pixel > edge_threshold:
                edge_count += 1
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
    
    if edge_count < min_content_area or max_x <= min_x or max_y <= min_y:
        return None
        
    return ContentBounds(
        left=min_x,
        top=min_y,
        right=max_x,
        bottom=max_y
    )


def detect_window_transparency(image: Image.Image) -> EdgeTrims:
    """
    Detect transparent regions around a window screenshot.
    
    Looks for alpha < 255 to find window shadow/rounded corner regions.
    
    Args:
        image: PIL Image (must have alpha channel)
        
    Returns:
        EdgeTrims for transparent regions
    """
    if image.mode != 'RGBA':
        return EdgeTrims(0, 0, 0, 0)
        
    w, h = image.size
    
    # Find first fully opaque row from top
    top = 0
    for y in range(h):
        row_opaque = True
        for x in range(0, w, max(1, w // 20)):  # Sample
            if image.getpixel((x, y))[3] < 255:
                row_opaque = False
                break
        if row_opaque:
            top = y
            break
    
    # Find last fully opaque row from bottom
    bottom = 0
    for y in range(h - 1, -1, -1):
        row_opaque = True
        for x in range(0, w, max(1, w // 20)):
            if image.getpixel((x, y))[3] < 255:
                row_opaque = False
                break
        if row_opaque:
            bottom = h - 1 - y
            break
    
    # Find first fully opaque column from left
    left = 0
    for x in range(w):
        col_opaque = True
        for y in range(0, h, max(1, h // 20)):
            if image.getpixel((x, y))[3] < 255:
                col_opaque = False
                break
        if col_opaque:
            left = x
            break
    
    # Find last fully opaque column from right
    right = 0
    for x in range(w - 1, -1, -1):
        col_opaque = True
        for y in range(0, h, max(1, h // 20)):
            if image.getpixel((x, y))[3] < 255:
                col_opaque = False
                break
        if col_opaque:
            right = w - 1 - x
            break
    
    return EdgeTrims(left=left, right=right, top=top, bottom=bottom)
