#!/usr/bin/env python3
"""
Debug script for nested switch connectivity issue.
Created: 2025-08-14

Context: Bug #2 - Nested switch default case connectivity issue where
the outer switch's default case becomes unreachable after CASE node post-processing.

Investigation: Examine the CFG structure of nested switches to understand
connectivity and reachability issues.
"""

from tree_climber.cfg.builder import CFGBuilder


def analyze_nested_switches():
    """Analyze nested switches CFG structure."""

    code = """
    int nested_switches(int x, int y) {
        switch (x) {
            case 1:
                switch (y) {
                    case 10:
                        return x + y;
                    case 20:
                        return x - y;
                    default:
                        return x * y;
                }
                break;
            case 2:
                return x + 10;
            default:
                return x - 10;
        }
        return 0;
    }
    """

    print("Code being analyzed:")
    print(code)

    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    print(f"\nFunction: {cfg.function_name}")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Group nodes by type
    node_types = {}
    for node_id, node in cfg.nodes.items():
        node_type = node.node_type.name
        if node_type not in node_types:
            node_types[node_type] = []
        node_types[node_type].append((node_id, node.source_text))

    print("\nNodes by type:")
    for node_type, nodes in node_types.items():
        print(f"  {node_type}: {len(nodes)}")
        for node_id, text in nodes:
            print(f"    {node_id}: '{text}'")

    print("\nEdges:")
    for node_id, node in cfg.nodes.items():
        for successor in node.successors:
            # Get edge label if available
            label = node.get_edge_label(successor)
            label_str = f" [{label}]" if label else ""
            print(f"  {node_id} -> {successor}{label_str}")

    # Check reachability from entry
    print("\nReachability analysis:")
    entry_nodes = [n for n in cfg.nodes.values() if n.node_type.name == "ENTRY"]
    if entry_nodes:
        entry_id = entry_nodes[0].id
        reachable = set()
        stack = [entry_id]

        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)

            # Find successors
            if current in cfg.nodes:
                for successor in cfg.nodes[current].successors:
                    if successor not in reachable:
                        stack.append(successor)

        unreachable = set(cfg.nodes.keys()) - reachable
        print(f"  Reachable nodes: {len(reachable)}/{len(cfg.nodes)}")
        if unreachable:
            print(f"  Unreachable nodes: {unreachable}")
            for node_id in unreachable:
                node = cfg.nodes[node_id]
                print(f"    {node_id}: {node.node_type.name} - '{node.source_text}'")


if __name__ == "__main__":
    analyze_nested_switches()
