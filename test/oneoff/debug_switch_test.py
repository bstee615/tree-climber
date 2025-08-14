#!/usr/bin/env python3
"""
Debug script for switch statement CFG node analysis.
Created: 2025-08-14

Context: C CFG comprehensive tests failing for switch statements - expected
3 CASE nodes but getting 0. Need to see what nodes are actually generated.

Problem: Switch statements not creating expected CASE nodes. The switch body
seems to be processed but case statements are missing from the CFG.

Investigation: Generate CFG for simple switch and examine actual node types,
connections, and source text to understand what's happening vs. what's expected.
"""

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.cfg_types import NodeType


def debug_switch():
    builder = CFGBuilder("c")
    builder.setup_parser()

    code = """
    int main() {
        int x = 5;
        switch (x) {
            case 1:
                x = x + 1;
                break;
            case 2:
                x = x + 2;
                break;
            default:
                x = 0;
        }
        return x;
    }
    """

    cfg = builder.build_cfg(code)

    print(f"Total nodes: {len(cfg.nodes)}")
    print(f"Function name: {cfg.function_name}")
    print()

    # Count node types
    node_type_counts = {}
    for node in cfg.nodes.values():
        node_type = node.node_type
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    print("Node type distribution:")
    for node_type, count in node_type_counts.items():
        print(f"  {node_type.name}: {count}")

    print()
    print("All nodes:")
    for node_id, node in cfg.nodes.items():
        print(
            f"  Node {node_id}: {node.node_type.name} - '{node.source_text}' - successors: {list(node.successors)}"
        )


if __name__ == "__main__":
    debug_switch()
