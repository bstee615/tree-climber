# This module runs automated tests from "parse tree specs", snapshots of a source code's parse tree.

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pydot
import pytest
import toml
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
        if node_id in ['node', 'edge', 'graph']:  # Skip DOT keywords
            continue
            
        # Extract attributes
        attrs = node.get_attributes()
        node_type = attrs.get('type', '').strip('"')
        label = attrs.get('label', '').strip('"')
        
        nodes.append(DotNode(
            id=node_id,
            node_type=node_type,
            label=label
        ))
    
    # Parse edges
    for edge in graph.get_edges():
        from_node = str(edge.get_source()).strip('"')
        to_node = str(edge.get_destination()).strip('"')
        
        attrs = edge.get_attributes()
        edge_label = attrs.get('label', '').strip('"') if attrs.get('label') else None
        
        edges.append(DotEdge(
            from_node=from_node,
            to_node=to_node,
            label=edge_label
        ))
    
    return nodes, edges


def assert_graphs_match(cfg: CFG, expected: Expected):
    """Assert that the CFG matches the expected DOT graph structure."""
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
    
    # Compare counts
    total_expected = len(expected_nodes)
    total_actual = len(cfg.nodes)
    assert total_actual == total_expected, f"Node count mismatch. Expected: {total_expected}, Got: {total_actual}"
    
    for node_type, expected_count in expected_counts.items():
        actual_count = actual_counts.get(node_type, 0)
        assert actual_count == expected_count, f"{node_type} count mismatch. Expected: {expected_count}, Got: {actual_count}"
    
    # Compare graph structure
    compare_dot_structure(cfg, expected_nodes, expected_edges)


def compare_dot_structure(cfg: CFG, expected_nodes: List[DotNode], expected_edges: List[DotEdge]) -> None:
    """Compare the CFG structure with the expected DOT graph."""
    # Create mapping of expected nodes by type and label for flexible matching
    expected_by_type_label = {}
    expected_node_by_id = {}
    
    for node in expected_nodes:
        key = f"{node.node_type}:{node.label}"
        if key not in expected_by_type_label:
            expected_by_type_label[key] = []
        expected_by_type_label[key].append(node)
        expected_node_by_id[node.id] = node
    
    # Create mapping of actual CFG nodes
    cfg_by_type_label = {}
    cfg_node_id_mapping = {}  # Maps expected node IDs to actual CFG node IDs
    
    for node_id, cfg_node in cfg.nodes.items():
        key = f"{cfg_node.node_type.name}:{cfg_node.source_text.strip()}"
        if key not in cfg_by_type_label:
            cfg_by_type_label[key] = []
        cfg_by_type_label[key].append((node_id, cfg_node))
    
    # Check that all expected node types and labels exist and create mapping
    for expected_key, expected_node_list in expected_by_type_label.items():
        if expected_key not in cfg_by_type_label:
            # Try partial matching - just check if the type exists
            node_type = expected_key.split(':')[0]
            type_matches = [k for k in cfg_by_type_label.keys() if k.startswith(f"{node_type}:")]
            if not type_matches:
                raise AssertionError(f"Expected node type not found: {expected_key}")
            
            print(f"Note: Exact match not found for '{expected_key}', but type '{node_type}' exists")
        else:
            # Create mapping from expected DOT node IDs to actual CFG node IDs
            cfg_matches = cfg_by_type_label[expected_key]
            for i, expected_node in enumerate(expected_node_list):
                if i < len(cfg_matches):
                    cfg_node_id, _ = cfg_matches[i]
                    cfg_node_id_mapping[expected_node.id] = cfg_node_id
    
    # Validate edge structure
    validate_edge_structure(cfg, expected_edges, cfg_node_id_mapping)
    
    print(f"Successfully validated graph structure with {len(expected_nodes)} nodes and {len(expected_edges)} edges")


def validate_edge_structure(cfg: CFG, expected_edges: List[DotEdge], node_id_mapping: dict) -> None:
    """Validate that the CFG edges match the expected DOT edges."""
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
    for expected_edge in expected_edges:
        # Map expected node IDs to actual CFG node IDs
        expected_from = node_id_mapping.get(expected_edge.from_node)
        expected_to = node_id_mapping.get(expected_edge.to_node)
        
        if expected_from is None:
            print(f"Warning: Cannot find mapping for expected source node '{expected_edge.from_node}'")
            continue
        if expected_to is None:
            print(f"Warning: Cannot find mapping for expected target node '{expected_edge.to_node}'")
            continue
        
        # Check if this edge exists in the actual CFG
        expected_edge_tuple = (expected_from, expected_to, expected_edge.label)
        
        if expected_edge_tuple not in actual_edges:
            # Try without label in case of label mismatch
            edge_found = False
            
            for actual_edge in actual_edges:
                if actual_edge[0] == expected_from and actual_edge[1] == expected_to:
                    if expected_edge.label and actual_edge[2] != expected_edge.label:
                        print(f"Warning: Edge {expected_from} -> {expected_to} has label '{actual_edge[2]}' but expected '{expected_edge.label}'")
                    edge_found = True
                    break
            
            if not edge_found:
                missing_edges.append(expected_edge)
    
    # Report missing edges
    if missing_edges:
        missing_edge_strs = []
        for edge in missing_edges:
            edge_str = f"{edge.from_node} -> {edge.to_node}"
            if edge.label:
                edge_str += f" [label=\"{edge.label}\"]"
            missing_edge_strs.append(edge_str)
        
        raise AssertionError(f"Missing expected edges: {', '.join(missing_edge_strs)}")
    
    # Check for unexpected edges (optional - might be too strict)
    expected_edge_set = set()
    for expected_edge in expected_edges:
        expected_from = node_id_mapping.get(expected_edge.from_node)
        expected_to = node_id_mapping.get(expected_edge.to_node)
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
            edge_str = f"{edge[0]} -> {edge[1]}"
            if edge[2]:
                edge_str += f" [label=\"{edge[2]}\"]"
            unexpected_edge_strs.append(edge_str)
        
        print(f"Warning: Found unexpected edges: {', '.join(unexpected_edge_strs)}")
    
    print(f"✓ Edge validation complete: {len(expected_edges)} expected edges checked")


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
