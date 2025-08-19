#!/usr/bin/env python3
"""
Debug script for switch case creation.
Created: 2025-08-14

Context: Check if CASE nodes are being created properly before post-processing,
particularly for the default case in nested switches.

Investigation: Examine the CFG before and after post-processing to see
exactly where the default case connection is being lost.
"""

from tree_climber.ast_utils import parse_source_to_ast
from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.languages.c import CCFGVisitor


def debug_switch_before_postprocessing():
    """Debug switch case creation before post-processing."""

    code = """
    int main() {
        int x = 5, y = 3;
        switch (x) {
            case 5:
                switch (y) {
                    case 3:
                        x = y + 10;
                    default:
                        x = y - 10;
                }
                break;
            default:
                x = -1;
        }
        return x;
    }
    """

    print("Code being analyzed:")
    print(code)

    # Parse AST
    tree = parse_source_to_ast(code, "c")

    # Create CFG visitor but don't run post-processing yet
    visitor = CCFGVisitor()
    visitor.setup_cfg()

    # Build CFG without post-processing
    result = visitor.visit(tree.root_node)
    cfg = visitor.cfg

    print(f"\nBEFORE POST-PROCESSING:")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Find CASE nodes and switch heads
    case_nodes = []
    switch_heads = []
    statements = []

    for node_id, node in cfg.nodes.items():
        if node.node_type.name == "CASE":
            case_nodes.append((node_id, node.source_text))
        elif node.node_type.name == "SWITCH_HEAD":
            switch_heads.append((node_id, node.source_text))
        elif "x = -1" in node.source_text:
            statements.append((node_id, node.source_text, "default_stmt"))
        elif "x = y + 10" in node.source_text:
            statements.append((node_id, node.source_text, "case_3_stmt"))

    print(f"\nSwitch heads: {len(switch_heads)}")
    for node_id, text in switch_heads:
        print(f"  {node_id}: '{text}'")

    print(f"\nCASE nodes: {len(case_nodes)}")
    for node_id, text in case_nodes:
        print(f"  {node_id}: '{text}'")

    print(f"\nKey statements:")
    for node_id, text, desc in statements:
        print(f"  {node_id}: '{text}' ({desc})")

    # Check connectivity from switch heads to case nodes
    if switch_heads:
        print(f"\nSwitch connectivity BEFORE post-processing:")
        for switch_id, switch_text in switch_heads:
            switch_node = cfg.nodes[switch_id]
            print(f"  Switch {switch_id} ('{switch_text}'):")
            print(f"    Successors: {list(switch_node.successors)}")
            print(f"    Edge labels: {switch_node.edge_labels}")

            for succ_id in switch_node.successors:
                succ_node = cfg.nodes[succ_id]
                edge_label = switch_node.get_edge_label(succ_id)
                print(
                    f"      -> {succ_id}: '{succ_node.source_text}' [{succ_node.node_type.name}] label='{edge_label}'"
                )

    # Now run post-processing
    print(f"\n" + "=" * 60)
    print("RUNNING POST-PROCESSING...")
    visitor._passthrough_entry_exit_nodes()

    print(f"\nAFTER POST-PROCESSING:")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Check what happened to connectivity
    remaining_switch_heads = []
    remaining_statements = []

    for node_id, node in cfg.nodes.items():
        if node.node_type.name == "SWITCH_HEAD":
            remaining_switch_heads.append((node_id, node.source_text))
        elif "x = -1" in node.source_text:
            remaining_statements.append((node_id, node.source_text, "default_stmt"))

    print(f"\nRemaining switch heads:")
    for node_id, text in remaining_switch_heads:
        print(f"  {node_id}: '{text}'")

    print(f"\nRemaining key statements:")
    for node_id, text, desc in remaining_statements:
        print(f"  {node_id}: '{text}' ({desc})")

    if remaining_switch_heads:
        print(f"\nSwitch connectivity AFTER post-processing:")
        for switch_id, switch_text in remaining_switch_heads:
            switch_node = cfg.nodes[switch_id]
            print(f"  Switch {switch_id} ('{switch_text}'):")
            print(f"    Successors: {list(switch_node.successors)}")
            print(f"    Edge labels: {switch_node.edge_labels}")

            for succ_id in switch_node.successors:
                if succ_id in cfg.nodes:
                    succ_node = cfg.nodes[succ_id]
                    edge_label = switch_node.get_edge_label(succ_id)
                    print(
                        f"      -> {succ_id}: '{succ_node.source_text}' [{succ_node.node_type.name}] label='{edge_label}'"
                    )


if __name__ == "__main__":
    debug_switch_before_postprocessing()
