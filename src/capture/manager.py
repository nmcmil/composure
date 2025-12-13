"""Capture manager that handles platform-specific screenshot capture."""

from typing import Optional, Callable
from PIL import Image

from .portal import PortalCapture, CaptureResult, get_desktop_wallpaper


class CaptureManager:
    """
    Unified capture manager that handles screenshot capture
    across different display servers and compositors.
    """
    
    def __init__(self):
        self.portal = PortalCapture()
        self._last_result: Optional[CaptureResult] = None
        
    def capture_interactive(self, 
                           callback: Callable[[Optional[CaptureResult]], None]) -> None:
        """
        Start an interactive screenshot capture.
        
        Uses xdg-desktop-portal on Wayland, or X11 fallback.
        
        Args:
            callback: Called with CaptureResult or None
        """
        self.portal.capture_interactive(callback)
        
    def load_from_file(self, path: str) -> Optional[CaptureResult]:
        """
        Load an image from file as if it were captured.
        
        Args:
            path: Path to image file
            
        Returns:
            CaptureResult or None
        """
        try:
            image = Image.open(path)
            result = CaptureResult(
                image=image.copy(),
                path=path,
                mode='import',
                dpi_scale=1.0
            )
            self._last_result = result
            return result
        except Exception as e:
            print(f"Failed to load image: {e}")
            return None
            
    def get_desktop_wallpaper(self) -> Optional[str]:
        """Get the current desktop wallpaper path."""
        return get_desktop_wallpaper()
        
    @property
    def last_result(self) -> Optional[CaptureResult]:
        """Get the last capture result."""
        return self._last_result
