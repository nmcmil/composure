"""Models package."""
from .composition import (
    CompositionState, 
    InsetConfig, 
    ShadowConfig, 
    ShadowLayer,
    BackgroundConfig,
    OutputConfig,
    BACKGROUND_PRESETS,
    PLATFORM_PRESETS,
    RATIO_PRESETS,
)
from .preset import Preset, PresetManager
