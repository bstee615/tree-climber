#!/usr/bin/env python3
"""
Debug script for nested switch connectivity issue.
Created: 2025-08-14

Context: Bug #2 - The outer switch should have a "default" edge from switch(x)
to the "x = -1;" statement, but it's missing due to CASE node post-processing.

Investigation: Examine the exact connectivity and find where the default case
connection is being lost during post-processing.
"""

from tree_climber.cfg.builder import CFGBuilder


def debug_nested_switch_connectivity():
    """Debug nested switch connectivity in detail."""

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

    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    print(f"\nFunction: {cfg.function_name}")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Find the two switch heads
    switch_heads = []
    default_statement = None

    for node_id, node in cfg.nodes.items():
        if node.node_type.name == "SWITCH_HEAD":
            switch_heads.append((node_id, node.source_text))
        elif "x = -1" in node.source_text:
            default_statement = (node_id, node.source_text)

    print(f"\nSwitch heads found: {len(switch_heads)}")
    for node_id, text in switch_heads:
        print(f"  {node_id}: '{text}'")

    if default_statement:
        print(f"\nDefault statement: {default_statement[0]}: '{default_statement[1]}'")
    else:
        print("\nNo default statement found!")

    # Check connectivity from outer switch to default statement
    if len(switch_heads) >= 2 and default_statement:
        # Assume first switch head is outer switch(x)
        outer_switch_id = switch_heads[0][0]
        outer_switch_node = cfg.nodes[outer_switch_id]
        default_stmt_id = default_statement[0]

        print(f"\nOuter switch ({outer_switch_id}) connectivity:")
        print(f"  Successors: {list(outer_switch_node.successors)}")
        print(f"  Edge labels: {outer_switch_node.edge_labels}")

        # Check if default statement is reachable from outer switch
        if default_stmt_id in outer_switch_node.successors:
            edge_label = outer_switch_node.get_edge_label(default_stmt_id)
            print(f"  ✅ Default statement reachable with label: '{edge_label}'")
        else:
            print(f"  ❌ Default statement NOT reachable from outer switch")

            # Check what the outer switch connects to
            print(f"\n  Outer switch connects to:")
            for successor_id in outer_switch_node.successors:
                successor_node = cfg.nodes[successor_id]
                edge_label = outer_switch_node.get_edge_label(successor_id)
                print(
                    f"    {successor_id}: '{successor_node.source_text}' [label: '{edge_label}']"
                )

    # Check reachability from entry
    print(f"\nReachability analysis:")
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

            if current in cfg.nodes:
                for successor in cfg.nodes[current].successors:
                    if successor not in reachable:
                        stack.append(successor)

        unreachable = set(cfg.nodes.keys()) - reachable
        if unreachable:
            print(f"  Unreachable nodes: {len(unreachable)}")
            for node_id in unreachable:
                node = cfg.nodes[node_id]
                print(f"    {node_id}: {node.node_type.name} - '{node.source_text}'")
                if node_id == default_statement[0]:
                    print(f"      ❌ This is the default statement!")
        else:
            print(f"  All nodes reachable")


if __name__ == "__main__":
    debug_nested_switch_connectivity()
