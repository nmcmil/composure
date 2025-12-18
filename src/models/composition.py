"""Data models for composition state and presets."""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
from pathlib import Path


@dataclass
class ShadowLayer:
    """A single shadow layer configuration."""
    blur: float = 28.0
    spread: float = -8.0
    offset_y: float = 18.0
    opacity: float = 0.18


@dataclass 
class ShadowConfig:
    """Shadow configuration with multiple layers."""
    strength: float = 0.55
    layers: list[ShadowLayer] = field(default_factory=lambda: [
        ShadowLayer(blur=28, spread=-8, offset_y=18, opacity=0.18),
        ShadowLayer(blur=10, spread=-4, offset_y=6, opacity=0.12),
    ])


@dataclass
class InsetConfig:
    """Inset configuration for content cropping."""
    mode: str = "balance"  # "manual" | "balance"
    strength: float = 0.65
    manual_px: int = 24
    balanced_insets_px: dict = field(default_factory=lambda: {
        "l": 0, "r": 0, "t": 0, "b": 0
    })


@dataclass
class BackgroundConfig:
    """Background configuration."""
    type: str = "preset"  # "preset" | "desktop" | "image"
    preset_id: str = "slate"
    image_path: Optional[str] = None


@dataclass
class OutputConfig:
    """Output size/ratio configuration."""
    mode: str = "autoRatio"  # "autoRatio" | "fixedRatio" | "fixedSize" | "platform"
    ratio: tuple[int, int] = (16, 9)
    size_px: tuple[int, int] = (1920, 1080)
    platform: Optional[str] = None


@dataclass
class CompositionState:
    """Complete composition state for a screenshot."""
    padding_px: int = 120
    inset: InsetConfig = field(default_factory=InsetConfig)
    radius_px: int = 18
    shadow: ShadowConfig = field(default_factory=ShadowConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CompositionState':
        """Create from dictionary."""
        state = cls()
        
        if 'padding_px' in data:
            state.padding_px = data['padding_px']
        if 'radius_px' in data:
            state.radius_px = data['radius_px']
            
        if 'inset' in data:
            inset_data = data['inset']
            state.inset = InsetConfig(
                mode=inset_data.get('mode', 'balance'),
                strength=inset_data.get('strength', 0.65),
                manual_px=inset_data.get('manual_px', 24),
                balanced_insets_px=inset_data.get('balanced_insets_px', {"l": 0, "r": 0, "t": 0, "b": 0})
            )
            
        if 'shadow' in data:
            shadow_data = data['shadow']
            layers = [
                ShadowLayer(**layer) for layer in shadow_data.get('layers', [])
            ]
            state.shadow = ShadowConfig(
                strength=shadow_data.get('strength', 0.55),
                layers=layers if layers else ShadowConfig().layers
            )
            
        if 'background' in data:
            bg_data = data['background']
            state.background = BackgroundConfig(
                type=bg_data.get('type', 'preset'),
                preset_id=bg_data.get('preset_id', 'sky'),
                image_path=bg_data.get('image_path')
            )
            
        if 'output' in data:
            out_data = data['output']
            state.output = OutputConfig(
                mode=out_data.get('mode', 'autoRatio'),
                ratio=tuple(out_data.get('ratio', [16, 9])),
                size_px=tuple(out_data.get('size_px', [1920, 1080])),
                platform=out_data.get('platform')
            )
            
        return state


# Background preset definitions organized by layer
# Layer 1: Flat Colors (8)
# Layer 2: Subtle Gradients (8)
# Layer 3: Loud Gradients (8)

BACKGROUND_PRESETS = {
    # === Layer 1: Flat Colors ===
    'black': {
        'name': 'Black', 'type': 'solid', 'colors': ['#000000'], 'layer': 1,
    },
    'white': {
        'name': 'White', 'type': 'solid', 'colors': ['#FFFFFF'], 'layer': 1,
    },
    'slate': {
        'name': 'Slate', 'type': 'solid', 'colors': ['#374151'], 'layer': 1,
    },
    'zinc': {
        'name': 'Zinc', 'type': 'solid', 'colors': ['#71717A'], 'layer': 1,
    },
    'stone': {
        'name': 'Stone', 'type': 'solid', 'colors': ['#78716C'], 'layer': 1,
    },
    'navy': {
        'name': 'Navy', 'type': 'solid', 'colors': ['#1E3A5F'], 'layer': 1,
    },
    'forest': {
        'name': 'Forest', 'type': 'solid', 'colors': ['#14532D'], 'layer': 1,
    },
    'wine': {
        'name': 'Wine', 'type': 'solid', 'colors': ['#4C1D35'], 'layer': 1,
    },
    
    # === Layer 2: Subtle Gradients ===
    'mist': {
        'name': 'Mist', 'type': 'linear', 'colors': ['#E5E7EB', '#D1D5DB'], 'angle': 180, 'layer': 2,
    },
    'dusk': {
        'name': 'Dusk', 'type': 'linear', 'colors': ['#374151', '#1F2937'], 'angle': 180, 'layer': 2,
    },
    'ocean': {
        'name': 'Ocean', 'type': 'linear', 'colors': ['#1A4068', '#0F2027'], 'angle': 180, 'layer': 2,
    },
    'moss': {
        'name': 'Moss', 'type': 'linear', 'colors': ['#2D5016', '#1A3409'], 'angle': 180, 'layer': 2,
    },
    'plum': {
        'name': 'Plum', 'type': 'linear', 'colors': ['#4A154B', '#2D0A2E'], 'angle': 180, 'layer': 2,
    },
    'midnight': {
        'name': 'Midnight', 'type': 'linear', 'colors': ['#0F172A', '#020617'], 'angle': 180, 'layer': 2,
    },
    'charcoal': {
        'name': 'Charcoal', 'type': 'linear', 'colors': ['#27272A', '#18181B'], 'angle': 135, 'layer': 2,
    },
    'smoke': {
        'name': 'Smoke', 'type': 'linear', 'colors': ['#44403C', '#292524'], 'angle': 135, 'layer': 2,
    },
    
    # === Layer 3: Loud Gradients ===
    'sunset': {
        'name': 'Sunset', 'type': 'linear', 'colors': ['#F97316', '#DC2626'], 'angle': 135, 'layer': 3,
    },
    'aurora': {
        'name': 'Aurora', 'type': 'linear', 'colors': ['#22D3EE', '#A855F7'], 'angle': 135, 'layer': 3,
    },
    'berry': {
        'name': 'Berry', 'type': 'linear', 'colors': ['#EC4899', '#8B5CF6'], 'angle': 135, 'layer': 3,
    },
    'lime': {
        'name': 'Lime', 'type': 'linear', 'colors': ['#84CC16', '#10B981'], 'angle': 135, 'layer': 3,
    },
    'sky': {
        'name': 'Sky', 'type': 'linear', 'colors': ['#38BDF8', '#6366F1'], 'angle': 135, 'layer': 3,
    },
    'fire': {
        'name': 'Fire', 'type': 'radial', 'colors': ['#FBBF24', '#DC2626'], 'layer': 3,
    },
    'neon': {
        'name': 'Neon', 'type': 'linear', 'colors': ['#F43F5E', '#8B5CF6', '#3B82F6'], 'angle': 135, 'layer': 3,
    },
    'tropical': {
        'name': 'Tropical', 'type': 'linear', 'colors': ['#14B8A6', '#FBBF24'], 'angle': 135, 'layer': 3,
    },
}

# Platform size presets
PLATFORM_PRESETS = {
    'twitter': {'name': 'Twitter', 'width': 1200, 'height': 675},
    'facebook': {'name': 'Facebook', 'width': 1200, 'height': 630},
    'instagram': {'name': 'Instagram', 'width': 1080, 'height': 1080},
    'linkedin': {'name': 'LinkedIn', 'width': 1200, 'height': 627},
    'youtube': {'name': 'YouTube', 'width': 1280, 'height': 720},
    'pinterest': {'name': 'Pinterest', 'width': 1000, 'height': 1500},
    'reddit': {'name': 'Reddit', 'width': 1200, 'height': 628},
    'snapchat': {'name': 'Snapchat', 'width': 1080, 'height': 1920},
}

# Aspect ratio presets
RATIO_PRESETS = {
    'auto': {'name': 'Auto', 'ratio': None},
    '1:1': {'name': '1:1', 'ratio': (1, 1)},
    '4:3': {'name': '4:3', 'ratio': (4, 3)},
    '3:2': {'name': '3:2', 'ratio': (3, 2)},
    '16:9': {'name': '16:9', 'ratio': (16, 9)},
    '21:9': {'name': '21:9', 'ratio': (21, 9)},
}
