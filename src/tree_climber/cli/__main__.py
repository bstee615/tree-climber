#!/usr/bin/env python3
"""
Tree Climber - Program Analysis Tool

A command-line interface for analyzing source code and generating visualizations
of Abstract Syntax Trees (AST), Control Flow Graphs (CFG), Def-Use Chains (DFG),
and Code Property Graphs (CPG).

Feature parity with tree-climber: https://github.com/bstee615/tree-climber
"""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from tree_climber import __version__ as VERSION
from tree_climber.cli.commands import (
    SUPPORTED_LAYOUTS,
    AnalysisOptions,
    analyze_source_code,
)
from tree_climber.cli.source import (
    ClipboardSource,
    CodeSource,
    FileSource,
    StdinSource,
    is_stdin_available,
    read_stdin,
)
from tree_climber.cli.visualizers.constants import SUPPORTED_LANGUAGES

# Create the main Typer app
app = typer.Typer(
    name="tree-climber",
    help="Program analysis tool for generating AST, CFG, DFG, and CPG visualizations",
    add_completion=False,
    rich_markup_mode="rich",
)


def typer_main(
    filename: Annotated[
        Optional[Path],
        typer.Argument(
            help="Source code file or directory to analyze, 'clipboard' to read from clipboard, or pipe via stdin",
        ),
    ] = None,
    # Analysis options
    draw_ast: Annotated[
        bool,
        typer.Option("--draw_ast", help="Visualize Abstract Syntax Tree"),
    ] = False,
    draw_cfg: Annotated[
        bool,
        typer.Option("--draw_cfg", help="Visualize Control Flow Graph"),
    ] = False,
    draw_dfg: Annotated[
        bool,
        typer.Option("--draw_dfg", help="Visualize Data Flow Graph/Def-Use Chains"),
    ] = False,
    draw_duc: Annotated[
        bool,
        typer.Option(
            "--draw_duc", help="Visualize Def-Use Chains (alias for --draw_dfg)"
        ),
    ] = False,
    draw_cpg: Annotated[
        bool,
        typer.Option("--draw_cpg", help="Visualize Code Property Graph (AST+CFG+DFG)"),
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
    tree-climber test/example.c --draw-ast

    # CFG:\n
    tree-climber test/example.c --draw-cfg

    # CFG + DFG view (CFG nodes + dashed DFG edges):\n
    tree-climber test/example.c --draw-cfg --draw-dfg

    # DFG-only view (Def-Use Chains):\n
    tree-climber test/example.c --draw-dfg\n
    tree-climber test/example.c --draw-duc  # alias for --draw-dfg

    # Combined views with overlays, subtree layout (default):\n
    tree-climber test/example.c --draw-cpg

    # Combined views with overlays, bigraph layout:\n
    tree-climber test/example.c --draw-cpg -L bigraph

    # Specify language and output directory explicitly:\n
    tree-climber test/test.java --language java --draw-ast --draw-cfg --draw-dfg --draw-cpg --output ./out

    # Read code from clipboard (language must be specified):\n
    tree-climber clipboard --language java --draw-ast
    tree-climber clipboard -l c --draw-cfg --draw-dfg

    # Read code from stdin pipe (language must be specified):\n
    echo 'int main() { return 0; }' | tree-climber - --language c --draw-ast
    cat mycode.java | tree-climber - -l java --draw-cfg
    """
    # Handle draw_duc as alias for draw_dfg
    draw_dfg = draw_dfg or draw_duc

    # Check for special filenames and stdin input
    stdin_available = is_stdin_available()
    clipboard_requested = filename and str(filename) == "clipboard"
    stdin_requested = filename and str(filename) == "-"

    # Validate input source - exactly one valid input method
    if stdin_requested:
        if not stdin_available:
            typer.echo(
                "Error: Filename '-' specified but no stdin input detected", err=True
            )
            raise typer.Exit(1)
        if Path("-").exists():
            typer.echo(
                "Error: 'stdin' signifies stdin input but a file named 'stdin' exists",
                err=True,
            )
            raise typer.Exit(1)

    if clipboard_requested and Path("clipboard").exists():
        typer.echo(
            "Error: 'clipboard' signifies clipboard input but a file named 'clipboard' exists",
            err=True,
        )
        raise typer.Exit(1)

    if not filename and not stdin_available:
        typer.echo(
            "Error: Must specify filename, 'clipboard' for clipboard input, '-' for stdin, or pipe input via stdin",
            err=True,
        )
        raise typer.Exit(1)

    # Validate inputs
    if not any([draw_ast, draw_cfg, draw_dfg, draw_cpg]):
        typer.echo(
            "Error: At least one visualization option must be specified "
            "(--draw-ast, --draw-cfg, --draw-dfg/--draw-duc, or --draw-cpg)",
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

    # Create code source based on input type
    code_source: CodeSource
    if clipboard_requested:
        from tree_climber.cli.clipboard import ClipboardError, get_clipboard_content

        try:
            source_code = get_clipboard_content()
            if not source_code.strip():
                typer.echo("Error: Clipboard is empty", err=True)
                raise typer.Exit(1)
            code_source = ClipboardSource(source_code)
        except ClipboardError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

        # For clipboard input, we need to detect language or require it
        if not language:
            typer.echo(
                "Error: Language must be specified when using 'clipboard' "
                "(cannot auto-detect from clipboard content)",
                err=True,
            )
            raise typer.Exit(1)
    elif stdin_requested or (not filename and stdin_available):
        source_code = read_stdin()
        if not source_code.strip():
            typer.echo("Error: Stdin is empty", err=True)
            raise typer.Exit(1)
        code_source = StdinSource(source_code)

        # For stdin input, we need to detect language or require it
        if not language:
            typer.echo(
                "Error: Language must be specified when using stdin "
                "(cannot auto-detect from piped content)",
                err=True,
            )
            raise typer.Exit(1)
    else:
        # At this point, filename is guaranteed to be not None by validation logic
        assert filename is not None
        code_source = FileSource(filename)

        # Auto-detect language if not specified for file input
        if not language:
            language = code_source.get_language_hint()
            if not language:
                typer.echo(
                    f"Error: Could not auto-detect language for '{filename}'. "
                    f"Please specify with --language option.",
                    err=True,
                )
                raise typer.Exit(1)

    # Set up output directory
    if output_dir is None:
        output_dir = code_source.get_output_dir()

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
        analyze_source_code(code_source, options)
    except Exception as e:
        if verbose:
            import traceback

            typer.echo(f"Error: {e}", err=True)
            typer.echo(traceback.format_exc(), err=True)
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    typer.echo(f"Tree Climber v{VERSION}")
    typer.echo("Program analysis tool with AST, CFG, DFG, and CPG visualization")


@app.command()
def languages():
    """List supported programming languages."""
    typer.echo("Supported programming languages:")
    for lang in SUPPORTED_LANGUAGES:
        typer.echo(f"  • {lang}")


def main() -> None:
    typer.run(typer_main)


if __name__ == "__main__":
    main()
