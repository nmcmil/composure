# Composure

<p align="center">
  <img src="data/icons/composure.png" width="128" alt="Composure Icon">
</p>

<p align="center">
  <strong>A Screenshot Beautifier for Linux</strong><br>
  Capture screenshots and compose them with stunning backgrounds, shadows, and rounded corners.
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/nmcmil/composure/main/docs/screenshot.png" alt="Composure Screenshot">
</p>

## ✨ Features

- **Auto-capture** — Watches your Screenshots folder and opens automatically
- **Beautiful backgrounds** — Gradient presets or solid colors
- **Rounded corners** — Adjustable corner radius
- **Drop shadows** — Soft, customizable shadows
- **Smart insets** — Content-aware trimming
- **Presets** — Save and load your favorite styles
- **System tray** — Runs quietly in the background
- **Copy to clipboard** — Wayland-compatible clipboard support

## 📦 Installation

### Dependencies

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
    python3-pil python3-numpy wl-clipboard gir1.2-ayatanaappindicator3-0.1
```

### Quick Start

```bash
git clone https://github.com/nmcmil/composure.git
cd composure
./scripts/install.sh
```

This will:
- Install the system tray indicator
- Set up auto-start on login
- Start watching for screenshots

## 🚀 Usage

1. **Take a screenshot** with your system tool (Print key)
2. **Composure opens automatically** with your screenshot
3. **Adjust styling** — background, padding, shadows, corners
4. **Save or copy** your beautified image

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open image file |
| `Ctrl+C` | Copy to clipboard |
| `Ctrl+S` | Save image |

### System Tray

The Composure indicator runs in your system tray and:
- Watches `~/Pictures/Screenshots` for new files
- Opens Composure when a screenshot is detected
- Provides quick access via the tray menu

## ⚙️ Preferences

Access preferences from the hamburger menu or tray icon:

- **Launch at Login** — Start indicator when you log in
- **Keyboard Shortcuts** — Customize copy/save shortcuts

## 📁 Files

- **Config**: `~/.config/composure/config.json`
- **Presets**: `~/.config/composure/presets/`
- **Autostart**: `~/.config/autostart/composure-indicator.desktop`

## 🔧 Manual Run

```bash
# Run the main app
python3 -m src.main

# Run just the indicator
python3 scripts/composure-indicator.py
```

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## 📄 License

GPL-3.0
