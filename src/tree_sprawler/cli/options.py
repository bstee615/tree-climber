from dataclasses import dataclass
from pathlib import Path

from .constants import (
    LayoutAlgorithm,
    OutputFormat,
)


@dataclass
class AnalysisOptions:
    """Configuration options for source code analysis."""

    draw_ast: bool
    draw_cfg: bool
    draw_duc: bool
    draw_cpg: bool
    language: str
    output_format: OutputFormat
    layout: LayoutAlgorithm
    output_dir: Path
    save: bool
    show: bool
    verbose: bool
    quiet: bool
    timing: bool
