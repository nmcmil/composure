"""Screenshot capture using xdg-desktop-portal."""

import gi
gi.require_version('Gtk', '4.0')

from gi.repository import Gio, GLib
from typing import Optional, Callable
from PIL import Image
from dataclasses import dataclass
import tempfile
import os


@dataclass
class CaptureResult:
    """Result from a screenshot capture."""
    image: Image.Image
    path: Optional[str]
    mode: str  # 'region' | 'window' | 'screen'
    dpi_scale: float


class PortalCapture:
    """
    Screenshot capture using xdg-desktop-portal.
    
    Works across Wayland compositors (GNOME, KDE, etc.)
    """
    
    PORTAL_BUS_NAME = 'org.freedesktop.portal.Desktop'
    PORTAL_OBJECT_PATH = '/org/freedesktop/portal/desktop'
    PORTAL_INTERFACE = 'org.freedesktop.portal.Screenshot'
    
    def __init__(self):
        self._pending_callback: Optional[Callable] = None
        self._request_path: Optional[str] = None
        self._signal_id: Optional[int] = None
        
    def capture_interactive(self, 
                           callback: Callable[[Optional[CaptureResult]], None],
                           modal: bool = True) -> None:
        """
        Start an interactive screenshot capture.
        
        The portal will show its own UI for selection.
        
        Args:
            callback: Called with CaptureResult or None on cancel/error
            modal: Whether to show modal dialog
        """
        self._pending_callback = callback
        
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            
            # Generate unique handle token
            import random
            handle_token = f"composure_{random.randint(0, 2**32)}"
            sender_name = bus.get_unique_name().replace('.', '_').replace(':', '')
            self._request_path = f"/org/freedesktop/portal/desktop/request/{sender_name}/{handle_token}"
            
            # Subscribe to Response signal
            self._signal_id = bus.signal_subscribe(
                self.PORTAL_BUS_NAME,
                'org.freedesktop.portal.Request',
                'Response',
                self._request_path,
                None,
                Gio.DBusSignalFlags.NONE,
                self._on_response,
                None
            )
            
            # Build options
            options = GLib.Variant('a{sv}', {
                'handle_token': GLib.Variant('s', handle_token),
                'modal': GLib.Variant('b', modal),
                'interactive': GLib.Variant('b', True),
            })
            
            # Call Screenshot method
            bus.call(
                self.PORTAL_BUS_NAME,
                self.PORTAL_OBJECT_PATH,
                self.PORTAL_INTERFACE,
                'Screenshot',
                GLib.Variant('(sa{sv})', ('', options)),
                GLib.VariantType.new('(o)'),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                self._on_screenshot_call_complete,
                None
            )
            
        except Exception as e:
            print(f"Portal capture failed: {e}")
            if callback:
                callback(None)
                
    def _on_screenshot_call_complete(self, bus, result, user_data):
        """Handle completion of the Screenshot D-Bus call."""
        try:
            bus.call_finish(result)
        except Exception as e:
            print(f"Screenshot call failed: {e}")
            if self._pending_callback:
                self._pending_callback(None)
                self._pending_callback = None
                
    def _on_response(self, connection, sender, path, interface, signal, params, user_data):
        """Handle the Response signal from the portal."""
        # Unsubscribe
        if self._signal_id:
            connection.signal_unsubscribe(self._signal_id)
            self._signal_id = None
            
        try:
            response, results = params.unpack()
            
            if response != 0:
                # User cancelled or error
                if self._pending_callback:
                    self._pending_callback(None)
                    self._pending_callback = None
                return
                
            # Get the URI
            uri = results.get('uri', None)
            if uri:
                uri_str = uri.get_string() if hasattr(uri, 'get_string') else str(uri)
                
                # Convert file:// URI to path
                if uri_str.startswith('file://'):
                    path = uri_str[7:]
                else:
                    path = uri_str
                    
                # Load the image
                try:
                    image = Image.open(path)
                    result = CaptureResult(
                        image=image.copy(),  # Copy to allow file cleanup
                        path=path,
                        mode='region',  # Portal doesn't distinguish
                        dpi_scale=1.0  # TODO: detect from display
                    )
                    
                    if self._pending_callback:
                        self._pending_callback(result)
                        
                except Exception as e:
                    print(f"Failed to load captured image: {e}")
                    if self._pending_callback:
                        self._pending_callback(None)
            else:
                if self._pending_callback:
                    self._pending_callback(None)
                    
        except Exception as e:
            print(f"Failed to process portal response: {e}")
            if self._pending_callback:
                self._pending_callback(None)
                
        self._pending_callback = None


def get_desktop_wallpaper() -> Optional[str]:
    """
    Get the current desktop wallpaper path.
    
    Tries GNOME settings first, then falls back to other DEs.
    
    Returns:
        Path to wallpaper image or None
    """
    try:
        # Try GNOME
        settings = Gio.Settings.new('org.gnome.desktop.background')
        uri = settings.get_string('picture-uri')
        
        # Handle dark mode variant
        if not uri:
            uri = settings.get_string('picture-uri-dark')
            
        if uri:
            if uri.startswith('file://'):
                return uri[7:]
            return uri
            
    except Exception:
        pass
        
    # Try KDE
    try:
        plasma_config = os.path.expanduser('~/.config/plasma-org.kde.plasma.desktop-appletsrc')
        if os.path.exists(plasma_config):
            with open(plasma_config, 'r') as f:
                for line in f:
                    if line.startswith('Image='):
                        path = line.split('=', 1)[1].strip()
                        if path.startswith('file://'):
                            return path[7:]
                        return path
    except Exception:
        pass
        
    return None
