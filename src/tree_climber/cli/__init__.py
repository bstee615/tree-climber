"""
Tree Climber CLI Package

Command-line interface for program analysis and visualization.
"""

from .commands import AnalysisOptions, analyze_source_code
from .visualizers.constants import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)

__all__ = [
    "analyze_source_code",
    "AnalysisOptions",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]
