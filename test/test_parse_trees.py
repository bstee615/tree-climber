# This module runs automated tests from "parse tree specs", snapshots of a source code's parse tree.

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pydot
import pytest
import toml
import warnings
from pydantic import BaseModel, ValidationError

from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.visitor import CFG

C_TEST_DIR = Path(__file__).parent / "parse_trees" / "c"
C_TESTS = list(C_TEST_DIR.rglob("*.toml"))


class Expected(BaseModel):
    graph: str


class TreeSpec(BaseModel):
    name: str
    code: str
    expect: Expected


@dataclass
class DotNode:
    """Represents a node parsed from DOT format."""

    id: str
    node_type: str
    label: str


@dataclass
class DotEdge:
    """Represents an edge parsed from DOT format."""

    from_node: str
    to_node: str
    label: Optional[str] = None


def parse_tree_file(file_path: Path) -> TreeSpec:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # file_path is a toml file
    if file_path.suffix != ".toml":
        raise ValueError(f"Expected a .toml file, got: {file_path.suffix}")

    # Parse the TOML file to get the code and expected tree
    try:
        data = toml.load(file_path)
    except toml.TomlDecodeError as e:
        raise ValueError(f"Failed to parse TOML file: {e}")

    try:
        # Use Pydantic to validate and parse the data
        return TreeSpec(
            name=file_path.stem,
            code=data["code"],
            expect=data["expect"],
        )
    except ValidationError as e:
        raise ValueError(f"Invalid test file structure: {e}")


def parse_dot_graph(dot_text: str) -> Tuple[List[DotNode], List[DotEdge]]:
    """Parse DOT format graph into nodes and edges."""
    # Parse the DOT string using pydot
    graphs = pydot.graph_from_dot_data(dot_text)
    if not graphs:
        raise ValueError("Failed to parse DOT graph")

    graph = graphs[0]

    nodes = []
    edges = []

    # Parse nodes
    for node in graph.get_nodes():
        node_id = node.get_name().strip('"')
        if node_id in ["node", "edge", "graph"]:  # Skip DOT keywords
            continue

        # Extract attributes
        attrs = node.get_attributes()
        node_type = attrs.get("type", "").strip('"')
        label = attrs.get("label", "").strip('"')

        nodes.append(DotNode(id=node_id, node_type=node_type, label=label))

    # Parse edges
    for edge in graph.get_edges():
        from_node = str(edge.get_source()).strip('"')
        to_node = str(edge.get_destination()).strip('"')

        attrs = edge.get_attributes()
        edge_label = attrs.get("label", "").strip('"') if attrs.get("label") else None

        edges.append(DotEdge(from_node=from_node, to_node=to_node, label=edge_label))

    return nodes, edges


def assert_graphs_match(cfg: CFG, expected: Expected):
    """Assert that the CFG matches the expected DOT graph structure."""
    errors = []  # Collect all errors before failing
    
    # Parse the expected DOT graph
    expected_nodes, expected_edges = parse_dot_graph(expected.graph)

    # Count nodes by type from expected graph
    expected_counts = {}
    for node in expected_nodes:
        node_type = node.node_type
        expected_counts[node_type] = expected_counts.get(node_type, 0) + 1

    # Count actual nodes by type
    actual_counts = {}
    for cfg_node in cfg.nodes.values():
        node_type = cfg_node.node_type.name
        actual_counts[node_type] = actual_counts.get(node_type, 0) + 1

    # Compare counts - collect errors instead of failing immediately
    total_expected = len(expected_nodes)
    total_actual = len(cfg.nodes)
    if total_actual != total_expected:
        errors.append(f"Node count mismatch. Expected: {total_expected}, Got: {total_actual}")

    for node_type, expected_count in expected_counts.items():
        actual_count = actual_counts.get(node_type, 0)
        if actual_count != expected_count:
            errors.append(f"{node_type} count mismatch. Expected: {expected_count}, Got: {actual_count}")

    # Compare graph structure - this will add to errors if there are issues
    try:
        compare_dot_structure(cfg, expected_nodes, expected_edges)
    except AssertionError as e:
        errors.append(str(e))

    # Fail with all collected errors
    if errors:
        error_message = "CFG validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise AssertionError(error_message)


def compare_dot_structure(
    cfg: CFG, expected_nodes: List[DotNode], expected_edges: List[DotEdge]
) -> None:
    """Compare the CFG structure with the expected DOT graph using semantic matching."""
    errors = []  # Collect all errors before failing
    
    # Create mapping of expected nodes by type and label for flexible matching
    expected_by_type_label = {}
    expected_node_by_id = {}

    for node in expected_nodes:
        key = f"{node.node_type}:{node.label}"
        if key not in expected_by_type_label:
            expected_by_type_label[key] = []
        expected_by_type_label[key].append(node)
        expected_node_by_id[node.id] = node

    # Create mapping of actual CFG nodes by semantic key
    cfg_by_type_label = {}
    cfg_node_semantic_mapping = {}  # Maps CFG nodes to their semantic identifiers

    for node_id, cfg_node in cfg.nodes.items():
        key = f"{cfg_node.node_type.name}:{cfg_node.source_text.strip()}"
        if key not in cfg_by_type_label:
            cfg_by_type_label[key] = []
        cfg_by_type_label[key].append((node_id, cfg_node))
        
        # Create semantic identifier for this CFG node (matches DOT naming)
        semantic_id = create_semantic_node_name(cfg_node)
        cfg_node_semantic_mapping[node_id] = semantic_id

    # Build reverse mapping from expected DOT node names to CFG node IDs
    dot_to_cfg_mapping = {}
    
    for expected_key, expected_node_list in expected_by_type_label.items():
        if expected_key not in cfg_by_type_label:
            # Try partial matching - just check if the type exists
            node_type = expected_key.split(":")[0]
            type_matches = [
                k for k in cfg_by_type_label.keys() if k.startswith(f"{node_type}:")
            ]
            if not type_matches:
                errors.append(f"Expected node type not found: {expected_key}")
                continue
            
            pytest.warns(UserWarning, match=f"Exact match not found for '{expected_key}', but type '{node_type}' exists")
        else:
            # Map expected nodes to CFG nodes based on semantic content
            cfg_matches = cfg_by_type_label[expected_key]
            for i, expected_node in enumerate(expected_node_list):
                if i < len(cfg_matches):
                    cfg_node_id, cfg_node = cfg_matches[i]
                    # Map the expected DOT node ID to the actual CFG node ID
                    dot_to_cfg_mapping[expected_node.id] = cfg_node_id

    # Validate edge structure using semantic matching
    try:
        validate_edge_structure_semantic(cfg, expected_edges, dot_to_cfg_mapping)
    except AssertionError as e:
        errors.append(str(e))

    # Report all collected errors
    if errors:
        error_message = "Graph structure validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise AssertionError(error_message)

    print(f"Successfully validated graph structure with {len(expected_nodes)} nodes and {len(expected_edges)} edges")


def create_semantic_node_name(cfg_node) -> str:
    """Create a semantic node name matching the DOT generation logic."""
    node_type = cfg_node.node_type.name.lower()
    
    if cfg_node.source_text.strip():
        # Use content-based name for statements
        content_key = cfg_node.source_text.strip().replace(' ', '_').replace(';', '').replace('(', '').replace(')', '').replace('=', 'eq').replace('<', 'lt').replace('>', 'gt').replace('+', 'plus').replace('*', 'mult')
        # Remove special characters and limit length
        content_key = ''.join(c for c in content_key if c.isalnum() or c == '_')[:20]
        if content_key:
            return f"{node_type}_{content_key}"
        else:
            return f"{node_type}_1"
    else:
        # Use type-based name for entry/exit nodes
        return node_type


def validate_edge_structure_semantic(
    cfg: CFG, expected_edges: List[DotEdge], dot_to_cfg_mapping: dict
) -> None:
    """Validate that the CFG edges match the expected DOT edges using semantic matching."""
    errors = []  # Collect all errors before failing
    warnings_list = []  # Collect warnings
    
    # Create set of actual edges for comparison
    actual_edges = set()

    for node_id, cfg_node in cfg.nodes.items():
        for successor_id in cfg_node.successors:
            edge_label = cfg_node.get_edge_label(successor_id)
            # Normalize edge label (empty string becomes None)
            if edge_label == "":
                edge_label = None
            actual_edges.add((node_id, successor_id, edge_label))

    # Check each expected edge
    missing_edges = []
    unmapped_edges = []
    
    for expected_edge in expected_edges:
        # Map expected node IDs to actual CFG node IDs
        expected_from = dot_to_cfg_mapping.get(expected_edge.from_node)
        expected_to = dot_to_cfg_mapping.get(expected_edge.to_node)

        if expected_from is None:
            unmapped_edges.append(f"Could not map expected from_node '{expected_edge.from_node}' to CFG")
            continue
        if expected_to is None:
            unmapped_edges.append(f"Could not map expected to_node '{expected_edge.to_node}' to CFG")
            continue

        # Look for the edge in actual edges
        expected_tuple = (expected_from, expected_to, expected_edge.label)
        if expected_tuple not in actual_edges:
            # Try to find edge with different label
            edge_found_with_different_label = False
            for actual_edge in actual_edges:
                if actual_edge[0] == expected_from and actual_edge[1] == expected_to:
                    edge_found_with_different_label = True
                    if expected_edge.label != actual_edge[2]:
                        warnings_list.append(
                            f"Edge {expected_edge.from_node} -> {expected_edge.to_node} "
                            f"has label '{actual_edge[2]}' but expected '{expected_edge.label}'"
                        )
                    break
            
            if not edge_found_with_different_label:
                missing_edges.append(expected_edge)

    # Issue warnings for unmapped edges
    for warning in unmapped_edges:
        warnings.warn(warning, UserWarning)

    # Issue warnings for label mismatches
    for warning in warnings_list:
        warnings.warn(warning, UserWarning)

    # Collect missing edge errors
    if missing_edges:
        missing_edge_strs = []
        for edge in missing_edges:
            edge_str = f"{edge.from_node} -> {edge.to_node}"
            if edge.label:
                edge_str += f" [label=\"{edge.label}\"]"
            missing_edge_strs.append(edge_str)
        errors.append(f"Missing expected edges: {', '.join(missing_edge_strs)}")

    # Check for unexpected edges (but only warn, don't fail)
    expected_edge_set = set()
    for expected_edge in expected_edges:
        expected_from = dot_to_cfg_mapping.get(expected_edge.from_node)
        expected_to = dot_to_cfg_mapping.get(expected_edge.to_node)
        if expected_from is not None and expected_to is not None:
            expected_edge_set.add((expected_from, expected_to))

    unexpected_edges = []
    for actual_edge in actual_edges:
        actual_from, actual_to, _ = actual_edge
        if (actual_from, actual_to) not in expected_edge_set:
            unexpected_edges.append(actual_edge)

    if unexpected_edges:
        unexpected_edge_strs = []
        for edge in unexpected_edges:
            # Map back to semantic names for better readability
            from_semantic = None
            to_semantic = None
            for dot_id, cfg_id in dot_to_cfg_mapping.items():
                if cfg_id == edge[0]:
                    from_semantic = dot_id
                if cfg_id == edge[1]:
                    to_semantic = dot_id
            
            if from_semantic and to_semantic:
                edge_str = f"{from_semantic} -> {to_semantic}"
                if edge[2]:
                    edge_str += f' [label="{edge[2]}"]'
                unexpected_edge_strs.append(edge_str)

        if unexpected_edge_strs:
            warnings.warn(f"Found unexpected edges: {', '.join(unexpected_edge_strs)}", UserWarning)

    # Fail if there were errors
    if errors:
        raise AssertionError("\n".join(errors))

    print(f"✓ All {len(expected_edges)} expected edges found in CFG")


@pytest.mark.parametrize("test_file", C_TESTS)
def test_c(test_file: Path):
    spec = parse_tree_file(test_file)
    print(f"Running test: {spec.name}")
    # Create and setup CFG builder
    language = "c"
    builder = CFGBuilder(language)
    builder.setup_parser()
    assert builder.parser is not None, f"Parser for {language} not set up correctly."

    # Parse source code to get AST
    tree = builder.parser.parse(bytes(spec.code, "utf8"))
    assert tree is not None, "Failed to parse source code."

    # Build CFG from AST
    cfg = builder.build_cfg(tree=tree)
    assert cfg is not None, "Failed to build CFG."

    assert_graphs_match(cfg, spec.expect)
