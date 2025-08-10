"""
CLI command implementations for Tree Sprawler.

This module contains the core logic for analyzing source code and generating
visualizations of AST, CFG, DUC, and CPG.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer

from tree_sprawler.ast_utils import ast_node_to_dict, parse_source_to_ast
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.dataflow.analyses.def_use import DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_sprawler.dataflow.solver import RoundRobinSolver

from .options import AnalysisOptions
from .visualizers import visualize_cpg


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
    if options.draw_cfg or options.draw_duc or options.draw_cpg:
        with AnalysisTimer("CFG construction", options.timing, options.verbose):
            cfg = _build_cfg(ast_root, options.language)

    # Perform dataflow analysis if needed for DUC
    dataflow_result = None
    if options.draw_duc or options.draw_cpg:
        with AnalysisTimer("Dataflow analysis", options.timing, options.verbose):
            dataflow_result = _analyze_dataflow(cfg)

    # Generate visualizations
    base_filename = filename.stem if filename.is_file() else filename.name

    # if options.draw_ast:
    #     with AnalysisTimer("AST visualization", options.timing, options.verbose):
    #         _visualize_ast(ast_root, base_filename, options)

    # if options.draw_cfg:
    #     with AnalysisTimer("CFG visualization", options.timing, options.verbose):
    #         _visualize_cfg(cfg, base_filename, options)

    # if options.draw_duc:
    #     with AnalysisTimer("DUC visualization", options.timing, options.verbose):
    #         _visualize_duc(cfg, dataflow_result, base_filename, options)

    if options.draw_cpg:
        with AnalysisTimer("CPG visualization", options.timing, options.verbose):
            visualize_cpg(filename, options)
            # _visualize_cpg(ast_root, cfg, dataflow_result, base_filename, options)

    if not options.quiet:
        typer.echo("✨ Analysis complete!")


def _parse_source_file(filename: Path, language: str):
    """Parse source code file to AST."""
    if not filename.is_file():
        raise ValueError(f"Not a file: {filename}")

    source_code = filename.read_text(encoding="utf-8")
    return parse_source_to_ast(source_code, language)


def _build_cfg(ast_root, language: str):
    """Build Control Flow Graph from AST."""
    builder = CFGBuilder(language)
    builder.setup_parser()
    return builder.build_cfg(tree=ast_root)


def _analyze_dataflow(cfg):
    """Perform reaching definitions dataflow analysis."""
    problem = ReachingDefinitionsProblem()
    solver = RoundRobinSolver()
    return solver.solve(cfg, problem)


def _visualize_ast(ast_root, base_filename: str, options: AnalysisOptions):
    """Generate AST visualization."""
    visualizer = ASTVisualizer(options.layout, options.output_format)

    if options.show:
        visualizer.show(ast_root, title=f"AST: {base_filename}")

    if options.save:
        output_path = (
            options.output_dir / f"{base_filename}_ast.{options.output_format.value}"
        )
        visualizer.save(ast_root, output_path, title=f"AST: {base_filename}")
        if not options.quiet:
            typer.echo(f"Saved AST visualization: {output_path}")


def _visualize_cfg(cfg, base_filename: str, options: AnalysisOptions):
    """Generate CFG visualization."""
    visualizer = CFGVisualizer(options.layout, options.output_format)

    if options.show:
        visualizer.show(cfg, title=f"CFG: {base_filename}")

    if options.save:
        output_path = (
            options.output_dir / f"{base_filename}_cfg.{options.output_format.value}"
        )
        visualizer.save(cfg, output_path, title=f"CFG: {base_filename}")
        if not options.quiet:
            typer.echo(f"Saved CFG visualization: {output_path}")


def _visualize_duc(cfg, dataflow_result, base_filename: str, options: AnalysisOptions):
    """Generate DUC visualization."""
    # Compute def-use chains
    duc_solver = DefUseSolver()
    duc_result = duc_solver.solve(cfg, dataflow_result)

    visualizer = DUCVisualizer(options.layout, options.output_format)

    if options.show:
        visualizer.show(cfg, duc_result, title=f"DUC: {base_filename}")

    if options.save:
        output_path = (
            options.output_dir / f"{base_filename}_duc.{options.output_format.value}"
        )
        visualizer.save(cfg, duc_result, output_path, title=f"DUC: {base_filename}")
        if not options.quiet:
            typer.echo(f"Saved DUC visualization: {output_path}")


def _visualize_cpg(
    ast_root, cfg, dataflow_result, base_filename: str, options: AnalysisOptions
):
    """Generate CPG visualization."""
    # Compute def-use chains
    duc_solver = DefUseSolver()
    duc_result = duc_solver.solve(cfg, dataflow_result)

    visualizer = CPGVisualizer(options.layout, options.output_format)

    if options.show:
        visualizer.show(ast_root, cfg, duc_result, title=f"CPG: {base_filename}")

    if options.save:
        output_path = (
            options.output_dir / f"{base_filename}_cpg.{options.output_format.value}"
        )
        visualizer.save(
            ast_root, cfg, duc_result, output_path, title=f"CPG: {base_filename}"
        )
        if not options.quiet:
            typer.echo(f"Saved CPG visualization: {output_path}")
