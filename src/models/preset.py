"""Preset management for Composure."""

from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
import json
import os

from .composition import CompositionState


PRESET_VERSION = 1


@dataclass
class Preset:
    """A saved composition preset."""
    name: str
    version: int
    composition: CompositionState
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'composition': self.composition.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Preset':
        """Create from dictionary."""
        return cls(
            name=data.get('name', 'Untitled'),
            version=data.get('version', PRESET_VERSION),
            composition=CompositionState.from_dict(data.get('composition', {}))
        )
    
    def save(self, path: Path) -> None:
        """Save preset to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
            
    @classmethod
    def load(cls, path: Path) -> 'Preset':
        """Load preset from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class PresetManager:
    """Manages loading and saving presets."""
    
    def __init__(self):
        self.presets_dir = self._get_presets_dir()
        self.presets: dict[str, Preset] = {}
        self._ensure_defaults()
        self.load_all()
        
    def _get_presets_dir(self) -> Path:
        """Get the presets directory path."""
        config_dir = Path(os.environ.get('XDG_CONFIG_HOME', 
                                          Path.home() / '.config'))
        return config_dir / 'composure' / 'presets'
    
    def _ensure_defaults(self) -> None:
        """Ensure default presets exist."""
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        default_path = self.presets_dir / 'default.json'
        if not default_path.exists():
            default = Preset(
                name='Default',
                version=PRESET_VERSION,
                composition=CompositionState()
            )
            default.save(default_path)
            
        # Create a "Minimal" preset
        minimal_path = self.presets_dir / 'minimal.json'
        if not minimal_path.exists():
            minimal_comp = CompositionState()
            minimal_comp.padding_px = 60
            minimal_comp.radius_px = 8
            minimal_comp.shadow.strength = 0.3
            minimal = Preset(
                name='Minimal',
                version=PRESET_VERSION,
                composition=minimal_comp
            )
            minimal.save(minimal_path)
            
        # Create a "Social" preset
        social_path = self.presets_dir / 'social.json'
        if not social_path.exists():
            social_comp = CompositionState()
            social_comp.padding_px = 80
            social_comp.radius_px = 16
            social_comp.shadow.strength = 0.7
            social_comp.background.preset_id = 'lavender'
            social = Preset(
                name='Social',
                version=PRESET_VERSION,
                composition=social_comp
            )
            social.save(social_path)
            
    def load_all(self) -> None:
        """Load all presets from disk."""
        self.presets.clear()
        
        if not self.presets_dir.exists():
            return
            
        for preset_file in self.presets_dir.glob('*.json'):
            try:
                preset = Preset.load(preset_file)
                preset_id = preset_file.stem
                self.presets[preset_id] = preset
            except Exception as e:
                print(f"Failed to load preset {preset_file}: {e}")
                
    def get(self, preset_id: str) -> Optional[Preset]:
        """Get a preset by ID."""
        return self.presets.get(preset_id)
    
    def save_preset(self, preset_id: str, preset: Preset) -> None:
        """Save a preset."""
        path = self.presets_dir / f'{preset_id}.json'
        preset.save(path)
        self.presets[preset_id] = preset
        
    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset."""
        # Don't delete built-in defaults
        if preset_id == 'default':
            return False
            
        path = self.presets_dir / f'{preset_id}.json'
        if path.exists():
            path.unlink()
            self.presets.pop(preset_id, None)
            return True
        return False
    
    def list_presets(self) -> list[tuple[str, str]]:
        """List all presets as (id, name) pairs."""
        return [(pid, p.name) for pid, p in sorted(self.presets.items())]
