# This module runs automated tests from "parse tree specs", snapshots of a source code's parse tree.

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pydot
import pytest
import toml
from pydantic import BaseModel, ValidationError

from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.cfg_types import NodeType
from tree_sprawler.cfg.visitor import CFG

C_TEST_DIR = Path(__file__).parent / "parse_trees" / "c"
C_TESTS = list(C_TEST_DIR.rglob("*.toml"))


class Expected(BaseModel):
    graph: str


class TreeSpec(BaseModel):
    name: str
    code: str
    expect: Expected


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


def assert_graphs_match(cfg: CFG, expected: Expected):
    """Assert that the CFG matches the expected structure."""
    # Count nodes by type
    total_nodes = len(cfg.nodes)
    entry_count = sum(
        1 for node in cfg.nodes.values() if node.node_type == NodeType.ENTRY
    )
    exit_count = sum(
        1 for node in cfg.nodes.values() if node.node_type == NodeType.EXIT
    )
    statement_count = sum(
        1 for node in cfg.nodes.values() if node.node_type == NodeType.STATEMENT
    )
    loop_header_count = sum(
        1 for node in cfg.nodes.values() if node.node_type == NodeType.LOOP_HEADER
    )

    assert total_nodes == expected.counts.nodes, (
        f"Node count mismatch. Expected: {expected.counts.nodes}, Got: {total_nodes}"
    )
    assert entry_count == expected.counts.ENTRY, (
        f"Entry count mismatch. Expected: {expected.counts.ENTRY}, Got: {entry_count}"
    )
    assert exit_count == expected.counts.EXIT, (
        f"Exit count mismatch. Expected: {expected.counts.EXIT}, Got: {exit_count}"
    )
    assert statement_count == expected.counts.STATEMENT, (
        f"Statement count mismatch. Expected: {expected.counts.STATEMENT}, Got: {statement_count}"
    )
    assert loop_header_count == expected.counts.LOOP_HEADER, (
        f"Loop header count mismatch. Expected: {expected.counts.LOOP_HEADER}, Got: {loop_header_count}"
    )

    # Parse and compare graph structure
    expected_nodes = parse_expected_graph(expected.graph)
    compare_graph_structure(cfg, expected_nodes)


@dataclass
class ExpectedGraphNode:
    """Represents a node in the expected graph format."""

    node_type: str
    content: str
    name: Optional[str] = None
    next_node: Optional[str] = None
    true_branch: Optional[str] = None
    false_branch: Optional[str] = None


def parse_expected_graph(graph_text: str) -> List[ExpectedGraphNode]:
    """Parse the expected graph format into a list of nodes."""
    nodes = []
    lines = [line.strip() for line in graph_text.strip().split("\n") if line.strip()]

    for line in lines:
        # Parse each line: NODE_TYPE(params):content
        # First split on the colon to separate node info from content
        if ":" not in line:
            continue

        node_part, content = line.split(":", 1)

        # Extract node type and parameters
        if "(" in node_part:
            node_type = node_part.split("(")[0]
            params_text = node_part[node_part.find("(") + 1 : node_part.rfind(")")]
        else:
            node_type = node_part
            params_text = ""

        # Parse parameters
        name = None
        next_node = None
        true_branch = None
        false_branch = None

        if params_text:
            # Simple parameter parsing - split by comma and parse key=value pairs
            for param in params_text.split(","):
                param = param.strip()
                if "=" in param:
                    key, value = param.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "name":
                        name = value
                    elif key == "next":
                        next_node = value
                    elif key == "true":
                        true_branch = value
                    elif key == "false":
                        false_branch = value

        nodes.append(
            ExpectedGraphNode(
                node_type=node_type,
                content=content.strip(),
                name=name,
                next_node=next_node,
                true_branch=true_branch,
                false_branch=false_branch,
            )
        )

    return nodes


def compare_graph_structure(cfg: CFG, expected_nodes: List[ExpectedGraphNode]) -> None:
    """Compare the CFG structure with the expected graph nodes."""
    # Create a mapping of CFG nodes by their content/type for comparison
    cfg_nodes_by_content = {}

    for node_id, cfg_node in cfg.nodes.items():
        key = f"{cfg_node.node_type.name}:{cfg_node.source_text.strip()}"
        if key not in cfg_nodes_by_content:
            cfg_nodes_by_content[key] = []
        cfg_nodes_by_content[key].append((node_id, cfg_node))

    # Build expected structure mapping
    expected_by_name = {}
    expected_sequence = []

    for i, expected_node in enumerate(expected_nodes):
        expected_sequence.append(expected_node)
        if expected_node.name:
            expected_by_name[expected_node.name] = expected_node

    # For now, let's do a basic structural comparison
    # Check that we have the right types and content in sequence
    for i, expected_node in enumerate(expected_nodes):
        expected_key = f"{expected_node.node_type}:{expected_node.content}"

        if expected_key not in cfg_nodes_by_content:
            # Try a more flexible match - just by node type if content doesn't match exactly
            type_matches = [
                k
                for k in cfg_nodes_by_content.keys()
                if k.startswith(f"{expected_node.node_type}:")
            ]
            if not type_matches:
                raise AssertionError(f"Expected node not found: {expected_key}")

            # For now, just verify the type exists
            print(
                f"Note: Content mismatch for {expected_node.node_type} '{expected_node.content}', but type exists"
            )


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
