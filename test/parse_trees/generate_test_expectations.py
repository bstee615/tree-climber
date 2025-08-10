#!/usr/bin/env python3
"""
Utility to generate DOT format expectations for CFG test files.

This script reads .test.toml files, builds the CFG from the code,
and generates the expected DOT graph format.
"""

import argparse
from pathlib import Path

import graphviz
import toml

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.visitor import CFG


def cfg_to_dot(cfg: CFG, graph_name: str = "CFG") -> str:
    """Convert a CFG to DOT format string with sequential node naming and location info."""
    lines = [f"digraph {graph_name} {{"]

    # Generate nodes with sequential naming by type
    node_id_map = {}  # Map CFG node IDs to DOT node names
    type_counters = {}  # Track sequential IDs by node type

    for node_id, cfg_node in cfg.nodes.items():
        # Create sequential node name by type
        node_type = cfg_node.node_type.name.lower()
        if node_type not in type_counters:
            type_counters[node_type] = 0
        type_counters[node_type] += 1

        dot_node_name = f"{node_type}_{type_counters[node_type]}"
        node_id_map[node_id] = dot_node_name

        # Clean up the label text for DOT format
        label = cfg_node.source_text.strip().replace('"', '\\"')
        if not label:
            label = cfg_node.node_type.name.lower()

        # Get location information from AST node
        line_info = ""
        if cfg_node.ast_node:
            start_line = (
                cfg_node.ast_node.start_point[0] + 1
            )  # Convert to 1-based line numbers
            line_info = f", line={start_line}"

        # Add the node definition with location
        lines.append(
            f'    {dot_node_name} [type="{cfg_node.node_type.name}", label="{label}"{line_info}]'
        )

    # Add empty line between nodes and edges
    lines.append("")

    # Generate edges
    for node_id, cfg_node in cfg.nodes.items():
        from_dot_name = node_id_map[node_id]

        for successor_id in cfg_node.successors:
            to_dot_name = node_id_map[successor_id]

            # Check if there's an edge label
            edge_label = cfg_node.get_edge_label(successor_id)
            if edge_label:
                lines.append(
                    f'    {from_dot_name} -> {to_dot_name} [label="{edge_label}"]'
                )
            else:
                lines.append(f"    {from_dot_name} -> {to_dot_name}")

    lines.append("}")
    return "\n".join(lines)


def generate_expectation_for_file(
    file_path: Path,
    write: bool,
    show: bool,
) -> None:
    """Generate DOT expectation for a single test file."""
    print(f"Processing: {file_path}")

    # Read the existing TOML file
    try:
        data = toml.load(file_path)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if "code" not in data:
        print(f"No 'code' field found in {file_path}")
        return

    # Extract the language from the file path or default to 'c'
    language = "c"  # Default for now, can be enhanced to detect from path

    try:
        # Build CFG from the code
        builder = CFGBuilder(language)
        builder.setup_parser()

        if builder.parser is None:
            raise RuntimeError(f"Failed to setup parser for language: {language}")

        tree = builder.parser.parse(bytes(data["code"], "utf8"))
        cfg = builder.build_cfg(tree=tree)

        # Generate DOT format
        dot_graph = cfg_to_dot(cfg)

        # Show graph if requested
        if show:
            print(f"Visualizing graph for {file_path}")
            show_dot_graph(dot_graph, file_path)

        if not write:
            print(f"Would update {file_path}")
            print(f"Generated DOT graph ({len(cfg.nodes)} nodes):")
            print("=" * 50)
            print(dot_graph)
            return

        # Update the data structure
        if "expect" not in data:
            data["expect"] = {}

        data["expect"]["graph"] = dot_graph

        # Write back to file with better formatting
        with open(file_path, "w") as f:
            # Write code first
            f.write(f'code="""\\\n{data["code"]}"""\n\n')

            # Write expect section
            f.write("[expect]\n")
            f.write(f'graph="""\\\n{data["expect"]["graph"]}\n"""\n')

        print(f"✓ Generated expectation for {file_path}")
        print(f"  Nodes: {len(cfg.nodes)}")
        print(f"  Entry nodes: {len(cfg.entry_node_ids)}")
        print(f"  Exit nodes: {len(cfg.exit_node_ids)}")

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        print(f"  Error details: {type(e).__name__}: {e}")


def show_dot_graph(dot_content: str, toml_file_path: Path) -> None:
    """Display a DOT graph by rendering to PNG and opening with system viewer."""
    # Generate PNG filename as sibling to TOML file
    png_path = toml_file_path.with_suffix(".png")

    try:
        # Create graphviz object from DOT source
        graph = graphviz.Source(dot_content)

        # Render to PNG (remove .png from path since render() adds it)
        graph.render(str(png_path)[:-4], format="png", cleanup=True)

        print(f"✓ Generated graph PNG: {png_path}")

    except Exception as e:
        print(f"Error showing graph: {e}")
        _fallback_show_dot(dot_content)


def _fallback_show_dot(dot_content: str) -> None:
    """Fallback function to show DOT content as text when rendering fails."""
    print("Falling back to showing DOT content as text:")
    print("=" * 50)
    print(dot_content)
    print("=" * 50)
    print("To visualize this graph, you can:")
    print("1. Install graphviz: sudo apt install graphviz")
    print("2. Install Python graphviz: pip install graphviz")
    print(
        "3. Copy the DOT content to an online visualizer: https://dreampuf.github.io/GraphvizOnline/"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate DOT format expectations for CFG test files"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Test files to process (default: all .test.toml files in test/parse_trees/)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write to file",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the graph as a PNG",
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path(__file__).parent / "parse_trees",
        help="Directory to search for test files (default: test/parse_trees/)",
    )

    args = parser.parse_args()

    if not args.write:
        print("Note: --write is not set, no files will be modified.")

    if args.files:
        # Process specific files
        for file_path in args.files:
            path = Path(file_path)
            if path.exists() and path.suffix == ".toml":
                generate_expectation_for_file(path, args.write, args.show)
            else:
                print(f"File not found or not a .toml file: {file_path}")
    else:
        # Process all .test.toml files in the directory
        test_files = list(args.directory.rglob("*.test.toml"))

        if not test_files:
            print(f"No .test.toml files found in {args.directory}")
            return

        print(f"Found {len(test_files)} test files")

        for test_file in test_files:
            generate_expectation_for_file(test_file, args.write, args.show)

        print(f"\nProcessed {len(test_files)} files")


if __name__ == "__main__":
    main()
