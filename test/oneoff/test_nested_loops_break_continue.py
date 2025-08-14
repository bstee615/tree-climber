#!/usr/bin/env python3
"""
Test script for nested loops with break/continue.
Created: 2025-08-14

Context: Verify that nested loops handle break/continue correctly
with proper context management.

Investigation: Test break and continue in nested loops to ensure
they connect to the correct targets.
"""

from tree_climber.cfg.builder import CFGBuilder


def test_nested_loops_break_continue():
    """Test nested loops with break and continue statements."""

    code = """
    int main() {
        for (int i = 0; i < 10; i++) {
            for (int j = 0; j < 5; j++) {
                if (i == 2) {
                    break;  // Should break from inner loop
                }
                if (j == 3) {
                    continue;  // Should continue inner loop
                }
                if (i == 5 && j == 2) {
                    goto cleanup;  // Test goto as well
                }
            }
            if (i == 7) {
                break;  // Should break from outer loop
            }
        }
    cleanup:
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

    # Find key nodes
    loop_headers = []
    break_nodes = []
    continue_nodes = []

    for node_id, node in cfg.nodes.items():
        if node.node_type.name == "LOOP_HEADER":
            loop_headers.append((node_id, node.source_text))
        elif node.node_type.name == "BREAK":
            break_nodes.append((node_id, node.source_text))
        elif node.node_type.name == "CONTINUE":
            continue_nodes.append((node_id, node.source_text))

    print(f"\nLoop headers: {len(loop_headers)}")
    for node_id, text in loop_headers:
        print(f"  {node_id}: '{text}'")

    print(f"\nBreak statements: {len(break_nodes)}")
    for node_id, text in break_nodes:
        print(f"  {node_id}: '{text}'")

    print(f"\nContinue statements: {len(continue_nodes)}")
    for node_id, text in continue_nodes:
        print(f"  {node_id}: '{text}'")

    # Check connectivity
    print("\nBreak/Continue connectivity:")
    for break_id, break_text in break_nodes:
        break_node = cfg.nodes[break_id]
        print(f"  Break {break_id} ('{break_text}'):")
        print(f"    Successors: {list(break_node.successors)}")
        for succ_id in break_node.successors:
            succ_node = cfg.nodes[succ_id]
            print(
                f"      -> {succ_id}: '{succ_node.source_text}' [{succ_node.node_type.name}]"
            )

    for continue_id, continue_text in continue_nodes:
        continue_node = cfg.nodes[continue_id]
        print(f"  Continue {continue_id} ('{continue_text}'):")
        print(f"    Successors: {list(continue_node.successors)}")
        for succ_id in continue_node.successors:
            succ_node = cfg.nodes[succ_id]
            print(
                f"      -> {succ_id}: '{succ_node.source_text}' [{succ_node.node_type.name}]"
            )

    # Check reachability
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
        else:
            print(f"  ✅ All {len(cfg.nodes)} nodes reachable")


if __name__ == "__main__":
    test_nested_loops_break_continue()
