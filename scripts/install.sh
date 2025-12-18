#!/bin/bash
# Composure Installation Script
# Sets up Composure indicator as a startup application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INDICATOR="$PROJECT_DIR/scripts/composure-indicator.py"

echo "=== Composure Indicator Installation ==="
echo ""

# Make scripts executable
chmod +x "$INDICATOR"
echo "✓ Made indicator executable"

# Check dependencies
echo ""
echo "Checking dependencies..."

check_python_module() {
    python3 -c "import gi; gi.require_version('$1', '$2')" 2>/dev/null
    return $?
}

MISSING=""
if ! check_python_module "AyatanaAppIndicator3" "0.1"; then
    MISSING="$MISSING gir1.2-ayatanaappindicator3-0.1"
fi
if ! check_python_module "Keybinder" "3.0"; then
    MISSING="$MISSING gir1.2-keybinder-3.0"
fi

if [ -n "$MISSING" ]; then
    echo "Installing missing dependencies:$MISSING"
    sudo apt install -y $MISSING
fi
echo "✓ Dependencies satisfied"

# Create autostart entry
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/composure-indicator.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Composure Indicator
Comment=Screenshot beautifier system tray
Exec=python3 $INDICATOR
Icon=camera-photo-symbolic
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF

echo "✓ Created autostart entry"

# Create desktop file for menu
LOCAL_APPS="$HOME/.local/share/applications"
mkdir -p "$LOCAL_APPS"

cat > "$LOCAL_APPS/io.github.composure.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Composure
Comment=Screenshot Beautifier for Linux
Exec=python3 -m src.main
Path=$PROJECT_DIR
Icon=camera-photo-symbolic
Terminal=false
Categories=Graphics;Utility;
Keywords=screenshot;capture;beautify;
EOF

echo "✓ Created desktop entry"

# Start the indicator now
echo ""
echo "Starting Composure indicator..."
nohup python3 "$INDICATOR" > /dev/null 2>&1 &
sleep 1

echo ""
echo "=== Installation Complete ==="
echo ""
echo "✓ Composure indicator is now running in your system tray"
echo "✓ It will start automatically on login"
echo ""
echo "Default shortcuts:"
echo "  • Print (PrtSc) - Take screenshot with Composure"
echo "  • Ctrl+Print   - Selection capture"
echo "  • Alt+Print    - Window capture"
echo ""
echo "You can change shortcuts in Composure Preferences."
