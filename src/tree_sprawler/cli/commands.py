"""
CLI command implementations for Tree Sprawler.

This module contains the core logic for analyzing source code and generating
visualizations of AST, CFG, DUC, and CPG.
"""

import time
from pathlib import Path

import typer
from tree_sitter import Tree

from tree_sprawler.ast_utils import parse_source_to_ast
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.dataflow.analyses.def_use import DefUseResult, DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_sprawler.dataflow.solver import RoundRobinSolver

from .options import AnalysisOptions
from .visualizers import (
    ASTVisualizer,
    BiGraphVisualizer,
    CFGVisualizer,
    DFGVisualizer,
    SubtreeVisualizer,
)

SUPPORTED_LAYOUTS = {"bigraph": BiGraphVisualizer, "subtree": SubtreeVisualizer}


class AnalysisTimer:
    """Context manager for timing analysis operations."""

    def __init__(
        self, operation_name: str, show_timing: bool = False, verbose: bool = False
    ):
        self.operation_name = operation_name
        self.show_timing = show_timing
        self.verbose = verbose
        self.start_time = 0.0

    def __enter__(self):
        if self.verbose:
            typer.echo(f"Starting {self.operation_name}...")
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if self.show_timing:
            typer.echo(f"✓ {self.operation_name} completed in {elapsed:.3f}s")
        elif self.verbose:
            typer.echo(f"✓ {self.operation_name} completed")


def analyze_source_code(filename: Path, options: AnalysisOptions) -> None:
    """
    Analyze source code and generate requested visualizations.

    Args:
        filename: Path to source file or directory to analyze
        options: Configuration options for the analysis
    """
    if not options.quiet:
        typer.echo(f"Analyzing: {filename}")

    # Ensure output directory exists
    if options.save:
        options.output_dir.mkdir(parents=True, exist_ok=True)

    # Parse source code to AST
    with AnalysisTimer("AST parsing", options.timing, options.verbose):
        ast_root = _parse_source_file(filename, options.language)

    # Build CFG if needed
    cfg = None
    if options.draw_cfg or options.draw_dfg or options.draw_cpg:
        with AnalysisTimer("CFG construction", options.timing, options.verbose):
            cfg = _build_cfg(ast_root, options.language)

    # Perform dataflow analysis if needed for DUC
    def_use_result = None
    if options.draw_dfg or options.draw_cpg:
        if cfg is None:
            raise ValueError("CFG is required for dataflow analysis")
        with AnalysisTimer("Dataflow analysis", options.timing, options.verbose):
            def_use_result = _analyze_dataflow(cfg)

    visualizer_options = (filename, options, ast_root, cfg, def_use_result)
    if options.draw_ast:
        with AnalysisTimer("AST visualization", options.timing, options.verbose):
            ASTVisualizer(*visualizer_options).visualize()
    if options.draw_cfg:
        with AnalysisTimer("CFG visualization", options.timing, options.verbose):
            CFGVisualizer(*visualizer_options).visualize()
    if options.draw_dfg:
        with AnalysisTimer("DFG visualization", options.timing, options.verbose):
            DFGVisualizer(*visualizer_options).visualize()
    if options.draw_cpg:
        with AnalysisTimer("CPG visualization", options.timing, options.verbose):
            SUPPORTED_LAYOUTS[options.layout](*visualizer_options).visualize()

    if not options.quiet:
        typer.echo("✨ Analysis complete!")


def _parse_source_file(filename: Path, language: str) -> Tree:
    """Parse source code file to AST."""
    if not filename.is_file():
        raise ValueError(f"Not a file: {filename}")

    source_code = filename.read_text(encoding="utf-8")
    return parse_source_to_ast(source_code, language)


def _build_cfg(ast_root: Tree, language: str) -> CFG:
    """Build Control Flow Graph from AST."""
    builder = CFGBuilder(language)
    builder.setup_parser()
    return builder.build_cfg(tree=ast_root)


def _analyze_dataflow(cfg: CFG) -> DefUseResult:
    """Perform reaching definitions dataflow analysis."""
    problem = ReachingDefinitionsProblem()
    dataflow_solver = RoundRobinSolver()
    def_use_solver = DefUseSolver()
    return def_use_solver.solve(cfg, dataflow_solver.solve(cfg, problem))
