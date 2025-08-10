"""
Constants for the Tree Sprawler CLI interface.

Following the DRY principle, all constants used throughout the CLI are defined here.
"""

from enum import Enum
from typing import List

# Supported programming languages
SUPPORTED_LANGUAGES: List[str] = ["c", "java"]
DEFAULT_LANGUAGE: str = "c"


# Output formats
class OutputFormat(str, Enum):
    """Supported output formats for visualizations."""

    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    JSON = "json"
    DOT = "dot"


SUPPORTED_OUTPUT_FORMATS: List[str] = [format.value for format in OutputFormat]
DEFAULT_OUTPUT_FORMAT: OutputFormat = OutputFormat.PNG


# Graph layout algorithms
class LayoutAlgorithm(str, Enum):
    """Supported graph layout algorithms."""

    DOT = "dot"  # Hierarchical layout (default)
    NEATO = "neato"  # Spring model layout
    FDP = "fdp"  # Force-directed layout
    SFDP = "sfdp"  # Scalable force-directed layout
    CIRCO = "circo"  # Circular layout
    TWOPI = "twopi"  # Radial layout


LAYOUT_ALGORITHMS: List[str] = [algo.value for algo in LayoutAlgorithm]
DEFAULT_LAYOUT: LayoutAlgorithm = LayoutAlgorithm.DOT

# Visualization constants
DEFAULT_FIGURE_SIZE: tuple[int, int] = (12, 8)
DEFAULT_DPI: int = 300
MAX_LABEL_LENGTH: int = 30
TRUNCATION_SUFFIX: str = "..."

# Color schemes for different graph types
AST_EDGE_COLOR: str = "black"
CFG_EDGE_COLOR: str = "blue"
DUC_EDGE_COLOR: str = "red"

# AST overlay (per-CFG-node) visualization constants
AST_OVERLAY_NODE_COLOR: str = "#E6E6E6"  # light gray fill for AST nodes
AST_OVERLAY_BORDER_COLOR: str = "#B0B0B0"  # border color for AST nodes
AST_OVERLAY_EDGE_COLOR: str = "#404040"  # dotted connector edges
AST_OVERLAY_FONT_SIZE: int = 8  # small font to reduce clutter
AST_OVERLAY_MAX_CHILDREN: int = 3  # limit how many child nodes we show per CFG node
AST_OVERLAY_SHOW_ONLY_NAMED: bool = True  # only show named AST children
AST_OVERLAY_LABEL_MAX: int = 24  # shorter labels for AST overlay

# Node colors
ENTRY_NODE_COLOR: str = "#90EE90"  # Light green
EXIT_NODE_COLOR: str = "#FFB6C1"  # Light pink
REGULAR_NODE_COLOR: str = "#87CEEB"  # Sky blue
CONDITION_NODE_COLOR: str = "#FFD700"  # Gold

ENTRY_NODE_SHAPE: str = "s"
EXIT_NODE_SHAPE: str = "s"
REGULAR_NODE_SHAPE: str = "o"
CONDITION_NODE_SHAPE: str = "D"

# Edge labels
TRUE_EDGE_LABEL: str = "True"
FALSE_EDGE_LABEL: str = "False"
BREAK_EDGE_LABEL: str = "break"
CONTINUE_EDGE_LABEL: str = "continue"
GOTO_EDGE_LABEL: str = "goto"
RETURN_EDGE_LABEL: str = "return"

# File extensions mapping
LANGUAGE_EXTENSIONS: dict[str, List[str]] = {
    "c": [".c", ".h"],
    "java": [".java"],
}

# Performance constants
DEFAULT_TIMEOUT_SECONDS: int = 300  # 5 minutes
LARGE_FILE_THRESHOLD_BYTES: int = 1024 * 1024  # 1MB
