#!/usr/bin/env python3
"""
Tree Sprawler - Program Analysis Tool

A command-line interface for analyzing source code and generating visualizations
of Abstract Syntax Trees (AST), Control Flow Graphs (CFG), Def-Use Chains (DUC),
and Code Property Graphs (CPG).

Feature parity with tree-climber: https://github.com/bstee615/tree-climber
"""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from src.tree_sprawler.cli.commands import (
    SUPPORTED_LAYOUTS,
    AnalysisOptions,
    analyze_source_code,
)
from src.tree_sprawler.cli.visualizers.constants import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
)

# Create the main Typer app
app = typer.Typer(
    name="tree-sprawler",
    help="Program analysis tool for generating AST, CFG, DUC, and CPG visualizations",
    add_completion=False,
    rich_markup_mode="rich",
)


def main(
    filename: Annotated[
        Path,
        typer.Argument(
            help="Source code file or directory to analyze",
            exists=True,
            readable=True,
        ),
    ],
    # Analysis options
    draw_ast: Annotated[
        bool,
        typer.Option("--draw-ast", help="Visualize Abstract Syntax Tree"),
    ] = False,
    draw_cfg: Annotated[
        bool,
        typer.Option("--draw-cfg", help="Visualize Control Flow Graph"),
    ] = False,
    draw_dfg: Annotated[
        bool,
        typer.Option("--draw-dfg", help="Visualize Def-Use Chains"),
    ] = False,
    draw_cpg: Annotated[
        bool,
        typer.Option("--draw-cpg", help="Visualize Code Property Graph (AST+CFG+DUC)"),
    ] = False,
    # Language and format options
    language: Annotated[
        Optional[str],
        typer.Option(
            "--language",
            "-l",
            help=f"Programming language ({', '.join(SUPPORTED_LANGUAGES)}). Auto-detected if not specified.",
        ),
    ] = None,
    # Output options
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Output directory for saved files (default: same as input file)",
        ),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", help="Display visualizations interactively"),
    ] = True,
    # Verbosity and debugging
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress all output except errors"),
    ] = False,
    # Performance options
    timing: Annotated[
        bool,
        typer.Option("--timing", help="Show timing information for each analysis step"),
    ] = False,
    layout: Annotated[
        str,
        typer.Option(
            "--layout",
            "-L",
            help=f"Layout style for visualizations ({', '.join(SUPPORTED_LAYOUTS)}).",
        ),
    ] = "subtree",
):
    """
    Analyze source code and generate program analysis visualizations.

    Examples:

    # AST:\n
    uv run -m main test/example.c --draw-ast

    # CFG:\n
    uv run -m main test/example.c --draw-cfg

    # CFG + DFG view (CFG nodes + dashed DFG edges):\n
    uv run -m main test/example.c --draw-cfg --draw-dfg

    # DFG-only view:\n
    uv run -m main test/example.c --draw-dfg

    # Combined views with overlays, subtree layout (default):\n
    uv run -m main test/example.c --draw-cpg

    # Combined views with overlays, bigraph layout:\n
    uv run -m main test/example.c --draw-cpg -L bigraph

    # Specify language and output directory explicitly:\n
    uv run -m main test/example.java --language java --draw-ast --draw-cfg --draw-dfg --draw-cpg --output ./out
    """
    # Validate inputs
    if not any([draw_ast, draw_cfg, draw_dfg, draw_cpg]):
        typer.echo(
            "Error: At least one visualization option must be specified "
            "(--draw-ast, --draw-cfg, --draw-duc, or --draw-cpg)",
            err=True,
        )
        raise typer.Exit(1)

    if quiet and verbose:
        typer.echo("Error: --quiet and --verbose cannot be used together", err=True)
        raise typer.Exit(1)

    if layout not in SUPPORTED_LAYOUTS:
        typer.echo(
            f"Error: Unsupported layout '{layout}'. "
            f"Supported layouts: {', '.join(SUPPORTED_LAYOUTS)}",
            err=True,
        )
        raise typer.Exit(1)

    if language and language not in SUPPORTED_LANGUAGES:
        typer.echo(
            f"Error: Unsupported language '{language}'. "
            f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}",
            err=True,
        )
        raise typer.Exit(1)

    # Auto-detect language if not specified
    if not language:
        language = _detect_language(filename)
        if not language:
            typer.echo(
                f"Error: Could not auto-detect language for '{filename}'. "
                f"Please specify with --language option.",
                err=True,
            )
            raise typer.Exit(1)

    # Set up output directory
    if output_dir is None:
        output_dir = filename.parent if filename.is_file() else filename

    # Create analysis options
    options = AnalysisOptions(
        draw_ast=draw_ast,
        draw_cfg=draw_cfg,
        draw_dfg=draw_dfg,
        draw_cpg=draw_cpg,
        language=language,
        layout=layout,
        output_dir=output_dir,
        show=show,
        verbose=verbose,
        quiet=quiet,
        timing=timing,
    )

    # Perform analysis
    try:
        analyze_source_code(filename, options)
    except Exception as e:
        if verbose:
            import traceback

            typer.echo(f"Error: {e}", err=True)
            typer.echo(traceback.format_exc(), err=True)
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _detect_language(filename: Path) -> Optional[str]:
    """Auto-detect programming language from file extension."""
    if filename.is_file():
        suffix = filename.suffix.lower()
        extension_map = {
            ".c": "c",
            ".h": "c",
            ".java": "java",
        }
        return extension_map.get(suffix)

    # For directories, we'd need to scan files
    return DEFAULT_LANGUAGE


@app.command()
def version():
    """Show version information."""
    typer.echo("Tree Sprawler v0.1.0")
    typer.echo("Program analysis tool with AST, CFG, DUC, and CPG visualization")


@app.command()
def languages():
    """List supported programming languages."""
    typer.echo("Supported programming languages:")
    for lang in SUPPORTED_LANGUAGES:
        typer.echo(f"  • {lang}")


if __name__ == "__main__":
    typer.run(main)
