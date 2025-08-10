from dataclasses import dataclass
from pathlib import Path


@dataclass
class AnalysisOptions:
    """Configuration options for source code analysis."""

    draw_ast: bool
    draw_cfg: bool
    draw_dfg: bool
    draw_cpg: bool
    language: str
    layout: str
    output_dir: Path
    show: bool
    verbose: bool
    quiet: bool
    timing: bool
