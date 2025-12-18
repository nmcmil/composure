# Changelog

All notable changes to Composure will be documented in this file.

## [0.9.0] - 2024-12-17

### Added
- **System tray indicator** — Composure now runs in the background and watches for new screenshots
- **Auto-capture** — Automatically opens when you take a screenshot with your system tool
- **Launch at Login** — Toggle in Preferences to start indicator on login
- **Preferences panel** — Configure shortcuts and startup behavior
- **Preset management** — Delete custom presets and set a default
- **Copy and Close** — New action to copy to clipboard and quit

### Changed
- Simplified main UI — removed redundant copy button from titlebar
- Cleaner empty state — simple text prompt instead of icon
- Removed Balance toggle from Inset section

### Fixed
- Clipboard now works reliably on Wayland
- Shortcut configuration persistence

## [0.1.0] - 2024-12-01

### Added
- Initial release
- Screenshot capture via xdg-desktop-portal
- Gradient background presets
- Adjustable padding, corner radius, and shadows
- Smart content-aware insets
- Preset save/load system
- Copy to clipboard (Wayland support)
- Save as PNG
