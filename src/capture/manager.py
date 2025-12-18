"""Capture manager that handles platform-specific screenshot capture."""

from typing import Optional, Callable
from PIL import Image
import subprocess
import threading
import time
import os
from pathlib import Path

from .portal import PortalCapture, CaptureResult, get_desktop_wallpaper


class CaptureManager:
    """
    Unified capture manager that handles screenshot capture
    across different display servers and compositors.
    """
    
    def __init__(self):
        self.portal = PortalCapture()
        self._last_result: Optional[CaptureResult] = None
        self._screenshot_dir = Path.home() / 'Pictures' / 'Screenshots'
        
    def capture_interactive(self, 
                           callback: Callable[[Optional[CaptureResult]], None]) -> None:
        """
        Start an interactive screenshot capture.
        
        Launches gnome-screenshot, waits for new file, then loads it.
        
        Args:
            callback: Called with CaptureResult or None
        """
        # Get list of existing screenshots before launching
        existing_files = set()
        if self._screenshot_dir.exists():
            existing_files = set(self._screenshot_dir.glob('*.png'))
        
        def watch_and_load():
            """Background thread to watch for new screenshot."""
            try:
                # Launch gnome-screenshot in interactive mode
                process = subprocess.run(
                    ['gnome-screenshot', '-i'],
                    capture_output=True,
                    timeout=120  # 2 minute timeout
                )
                
                # Give filesystem a moment
                time.sleep(0.5)
                
                # Find new files
                if self._screenshot_dir.exists():
                    current_files = set(self._screenshot_dir.glob('*.png'))
                    new_files = current_files - existing_files
                    
                    if new_files:
                        # Get the newest file
                        newest = max(new_files, key=lambda p: p.stat().st_mtime)
                        result = self.load_from_file(str(newest))
                        callback(result)
                        return
                
                # No new file found
                callback(None)
                
            except subprocess.TimeoutExpired:
                callback(None)
            except FileNotFoundError:
                # gnome-screenshot not found, try portal fallback
                self.portal.capture_interactive(callback)
            except Exception as e:
                print(f"Capture error: {e}")
                callback(None)
        
        # Run in background thread to not block UI
        thread = threading.Thread(target=watch_and_load, daemon=True)
        thread.start()
        
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
