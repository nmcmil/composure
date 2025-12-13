"""Composer package - image processing and rendering."""
from .detector import (
    detect_edge_background,
    detect_content_saliency,
    detect_window_transparency,
    ContentBounds,
    EdgeTrims,
)
from .balance import (
    compute_balanced_insets,
    compute_manual_insets,
    apply_insets,
    BalancedInsets,
)
from .renderer import CompositionRenderer
from .pipeline import CompositionPipeline
