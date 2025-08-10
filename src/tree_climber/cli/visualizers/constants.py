"""
Constants for the Tree Climber CLI interface.

Following the DRY principle, all constants used throughout the CLI are defined here.
"""

from enum import Enum
from typing import List

# Supported programming languages
SUPPORTED_LANGUAGES: List[str] = ["c", "java"]
DEFAULT_LANGUAGE: str = "c"


# Visualization constants
DEFAULT_FIGURE_SIZE: tuple[int, int] = (12, 8)
DEFAULT_DPI: int = 300
MAX_LABEL_LENGTH: int = 50
TRUNCATION_SUFFIX: str = "..."

# Color schemes for different graph types
AST_EDGE_COLOR: str = "black"
CFG_EDGE_COLOR: str = "blue"
DUC_EDGE_COLOR: str = "red"

# AST overlay (per-CFG-node) visualization constants
AST_OVERLAY_NODE_COLOR: str = "#E6E6E6"  # light gray fill for AST nodes
AST_OVERLAY_BORDER_COLOR: str = "#B0B0B0"  # border color for AST nodes
AST_OVERLAY_EDGE_COLOR: str = "#404040"  # dotted connector edges
AST_OVERLAY_LINKING_EDGE_COLOR: str = "blue"
AST_OVERLAY_FONT_SIZE: int = 8  # small font to reduce clutter
AST_OVERLAY_MAX_CHILDREN: int = 3  # limit how many child nodes we show per CFG node
AST_OVERLAY_SHOW_ONLY_NAMED: bool = True  # only show named AST children
AST_OVERLAY_LABEL_MAX: int = MAX_LABEL_LENGTH  # shorter labels for AST overlay

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

# Graphviz constants
SHAPE_MAP = {"s": "box", "o": "ellipse", "D": "diamond"}

# File extensions mapping
LANGUAGE_EXTENSIONS: dict[str, List[str]] = {
    "c": [".c", ".h"],
    "java": [".java"],
}

# Performance constants
DEFAULT_TIMEOUT_SECONDS: int = 300  # 5 minutes
LARGE_FILE_THRESHOLD_BYTES: int = 1024 * 1024  # 1MB
