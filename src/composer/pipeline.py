"""High-level composition pipeline."""

from PIL import Image
from pathlib import Path
from typing import Optional, Tuple

from ..models.composition import CompositionState
from .renderer import CompositionRenderer


class CompositionPipeline:
    """
    Orchestrates the full composition workflow.
    
    This is the main entry point for composing screenshots.
    """
    
    def __init__(self):
        self.input_image: Optional[Image.Image] = None
        self.input_path: Optional[Path] = None
        self.state = CompositionState()
        self._cached_result: Optional[Image.Image] = None
        self._cache_valid = False
        
    def _strip_transparent_borders(self, image: Image.Image) -> Image.Image:
        """
        Smart crop to remove GNOME shadows/padding.
        Strategy:
        1. Try to find the "Content Box" (Alpha > 250). This crops out 
           semi-transparent shadows and even anti-aliased corners.
        2. If that fails (e.g. transparent terminal), fallback to "Shadow Box"
           (Alpha > 50) to at least remove the invisible padding.
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        alpha = image.split()[-1]
        w, h = image.size
        
        # Strategy 1: Aggressive Crop (Content Only)
        # Threshold 250 removes everything except fully opaque pixels
        mask_opaque = alpha.point(lambda p: 255 if p > 250 else 0)
        bbox_opaque = mask_opaque.getbbox()
        
        # Check if opaque result is "reasonable" (not empty and not tiny)
        if bbox_opaque:
            ow = bbox_opaque[2] - bbox_opaque[0]
            oh = bbox_opaque[3] - bbox_opaque[1]
            # If we found substantial opaque content (>50x50px), use it
            if ow > 50 and oh > 50:
                return image.crop(bbox_opaque)
        
        # Strategy 2: Safe Fallback (Shadow Crop)
        # Threshold 50 removes invisible borders and very faint shadows
        mask_safe = alpha.point(lambda p: 255 if p > 50 else 0)
        bbox_safe = mask_safe.getbbox()
        
        if bbox_safe:
            # Add 1px padding to be safe
            left, upper, right, lower = bbox_safe
            return image.crop((
                max(0, left - 1),
                max(0, upper - 1),
                min(w, right + 1),
                min(h, lower + 1)
            ))
            
        return image

    def load_image(self, path: str) -> bool:
        """
        Load an input image from path.
        
        Args:
            path: Path to image file
            
        Returns:
            True if loaded successfully
        """
        try:
            image = Image.open(path)
            # Convert to RGBA for consistent handling
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
                
            # Strip transparent borders (removes existing shadows/padding)
            self.input_image = self._strip_transparent_borders(image)
            
            self.input_path = Path(path)
            self._cache_valid = False
            return True
        except Exception as e:
            print(f"Failed to load image: {e}")
            return False
            
    def set_image(self, image: Image.Image) -> None:
        """
        Set the input image directly (e.g., from capture).
        
        Args:
            image: PIL Image
        """
        # Strip borders before setting
        self.input_image = self._strip_transparent_borders(image)
        
        self.input_path = None
        self._cache_valid = False
        
    def update_state(self, **kwargs) -> None:
        """
        Update composition state parameters.
        
        Args:
            **kwargs: State parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self._cache_valid = False
        
    def set_state(self, state: CompositionState) -> None:
        """
        Replace the entire composition state.
        
        Args:
            state: New CompositionState
        """
        self.state = state
        self._cache_valid = False
        
    def invalidate_cache(self) -> None:
        """Mark the cached result as invalid."""
        self._cache_valid = False
        
    def render(self, force: bool = False) -> Optional[Image.Image]:
        """
        Render the composition.
        
        Args:
            force: If True, bypass cache
            
        Returns:
            Rendered PIL Image or None if no input image
        """
        if self.input_image is None:
            return None
            
        if self._cache_valid and not force and self._cached_result is not None:
            return self._cached_result
            
        renderer = CompositionRenderer(self.input_image, self.state)
        self._cached_result = renderer.render()
        self._cache_valid = True
        
        return self._cached_result
        
    def get_output_size(self) -> Optional[Tuple[int, int]]:
        """Get the output dimensions without rendering."""
        if self.input_image is None:
            return None
            
        renderer = CompositionRenderer(self.input_image, self.state)
        return renderer.compute_output_size()
        
    def export_png(self, path: str) -> bool:
        """
        Export the composition as PNG.
        
        Args:
            path: Output file path
            
        Returns:
            True if successful
        """
        result = self.render()
        if result is None:
            return False
            
        try:
            # Always save as RGBA to preserve transparency
            if result.mode != 'RGBA':
                result = result.convert('RGBA')
            result.save(path, 'PNG', optimize=True)
            return True
        except Exception as e:
            print(f"Failed to export: {e}")
            return False
            
    def export_bytes(self) -> Optional[bytes]:
        """
        Export the composition as PNG bytes.
        
        Returns:
            PNG bytes or None
        """
        import io
        
        result = self.render()
        if result is None:
            return None
            
        try:
            buf = io.BytesIO()
            # Always save as RGBA to preserve transparency
            if result.mode != 'RGBA':
                result = result.convert('RGBA')
            result.save(buf, 'PNG', optimize=True)
            return buf.getvalue()
        except Exception as e:
            print(f"Failed to export bytes: {e}")
            return None
