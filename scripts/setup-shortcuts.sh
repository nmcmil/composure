#!/bin/bash
# Setup GNOME keyboard shortcuts for Composure
# Uses ydotool to trigger GNOME's native screenshot shortcuts

SCRIPT_PATH="/home/nick/.gemini/antigravity/Composure/scripts/composure-capture.py"

BINDING_A="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/composure-a/"
BINDING_B="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/composure-b/"
BINDING_C="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/composure-c/"

# Build binding list
CURRENT=$(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings | tr -d "[]' ")

NEW_BINDINGS="['$BINDING_A', '$BINDING_B', '$BINDING_C'"

if [ -n "$CURRENT" ]; then
    for binding in $(echo "$CURRENT" | tr ',' '\n'); do
        if [[ "$binding" != *"composure"* ]] && [ -n "$binding" ]; then
            NEW_BINDINGS="$NEW_BINDINGS, '$binding'"
        fi
    done
fi
NEW_BINDINGS="$NEW_BINDINGS]"

gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "$NEW_BINDINGS"

# Ctrl+Shift+A = Full screen (triggers Shift+Print)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_A name "Composure - Full Screen"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_A command "python3 $SCRIPT_PATH desktop"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_A binding "<Control><Shift>a"

# Ctrl+Shift+B = Selection (triggers Print - interactive)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_B name "Composure - Selection"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_B command "python3 $SCRIPT_PATH selection"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_B binding "<Control><Shift>b"

# Ctrl+Shift+C = Window (triggers Alt+Print)
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_C name "Composure - Window"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_C command "python3 $SCRIPT_PATH window"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$BINDING_C binding "<Control><Shift>c"

echo "✓ Keyboard shortcuts configured!"
echo ""
echo "Shortcuts (triggers GNOME's native screenshot, then Composure):"
echo "  Ctrl+Shift+A  - Full screen capture → Composure"
echo "  Ctrl+Shift+B  - Selection capture → Composure"
echo "  Ctrl+Shift+C  - Window capture → Composure"
