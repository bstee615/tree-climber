#!/usr/bin/env python3
"""
Debug script for remaining test failures.
Created: 2025-08-14

Context: After fixing most test issues, 4 tests still fail with STATEMENT
node count mismatches. Need to analyze what the actual counts should be.

Problem: Tests expect specific STATEMENT counts but getting higher counts.
All failures show "Expected X nodes of type STATEMENT, got Y" where Y > X.

Investigation: Analyze the remaining failed test cases to determine
correct STATEMENT node counts and update test expectations.
"""

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.cfg_types import NodeType


def analyze_remaining_failure(test_name, code, expected_statements):
    """Analyze remaining failures to get correct STATEMENT counts."""
    print(f"\n{'=' * 60}")
    print(f"ANALYZING: {test_name}")
    print(f"EXPECTED STATEMENTS: {expected_statements}")
    print(f"{'=' * 60}")

    builder = CFGBuilder("c")
    builder.setup_parser()

    cfg = builder.build_cfg(code)

    # Count node types
    node_type_counts = {}
    for node in cfg.nodes.values():
        node_type = node.node_type
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    actual_statements = node_type_counts.get(NodeType.STATEMENT, 0)
    print(f"ACTUAL STATEMENTS: {actual_statements}")

    print("\nNode type distribution:")
    for node_type, count in node_type_counts.items():
        print(f"  {node_type.name}: {count}")

    print("\nAll STATEMENT nodes:")
    for node_id, node in sorted(cfg.nodes.items()):
        if node.node_type == NodeType.STATEMENT:
            print(f"  Node {node_id}: '{node.source_text}'")


def main():
    """Analyze the 4 remaining failures."""

    # 1. switch_in_loop failure
    analyze_remaining_failure(
        "switch_in_loop",
        """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
                switch (x) {
                    case 5:
                        x = x + 5;
                        break;
                    default:
                        break;
                }
            }
            return x;
        }
        """,
        4,  # expected 4 from test
    )

    # 2. state_machine_pattern failure
    analyze_remaining_failure(
        "state_machine_pattern",
        """
        int process_state(int state, int input) {
            int result = 0;
            
            switch (state) {
                case 0:  // IDLE
                    if (input == 1) {
                        state = 1;
                    }
                    break;
                    
                case 1:  // PROCESSING
                    result = input * 2;
                    if (result > 10) {
                        state = 2;
                    } else {
                        state = 0;
                    }
                    break;
                    
                case 2:  // DONE
                    return result;
                    
                default:
                    state = 0;
                    break;
            }
            
            return state;
        }
        """,
        3,  # expected 3 from test
    )

    # 3. nested_switches failure (different issue - unreachable node)
    print(f"\n{'=' * 60}")
    print("ANALYZING: nested_switches (unreachable node issue)")
    print(f"{'=' * 60}")

    builder = CFGBuilder("c")
    builder.setup_parser()

    code = """
    int main() {
        int x = 5, y = 3;
        switch (x) {
            case 5:
                switch (y) {
                    case 3:
                        x = x + y;
                        break;
                    default:
                        x = 0;
                        break;
                }
                break;
            default:
                x = -1;
        }
        return x;
    }
    """
    cfg = builder.build_cfg(code)

    print(f"Total nodes: {len(cfg.nodes)}")
    print("\nAll nodes with connections:")
    for node_id, node in sorted(cfg.nodes.items()):
        print(
            f"  Node {node_id}: {node.node_type.name} - '{node.source_text}' - "
            f"preds: {list(node.predecessors)}, succs: {list(node.successors)}"
        )

    # Check reachability manually
    entry_nodes = [n for n in cfg.nodes.values() if n.node_type.name == "ENTRY"]
    if entry_nodes:
        entry_id = entry_nodes[0].id
        reachable = set()
        stack = [entry_id]
        while stack:
            node_id = stack.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            node = cfg.nodes[node_id]
            for successor_id in node.successors:
                if successor_id not in reachable:
                    stack.append(successor_id)

        all_node_ids = set(cfg.nodes.keys())
        unreachable = all_node_ids - reachable
        print(f"\nReachable: {sorted(reachable)}")
        print(f"Unreachable: {sorted(unreachable)}")

    # 4. deeply_nested_structures failure
    analyze_remaining_failure(
        "deeply_nested_structures",
        """
        int main() {
            int x = 0;
            if (x == 0) {
                while (x < 10) {
                    for (int i = 0; i < 5; i++) {
                        if (i == 2) {
                            switch (x) {
                                case 0:
                                    x = 1;
                                    break;
                                default:
                                    x = x + 1;
                                    break;
                            }
                        }
                    }
                    x = x + 1;
                }
            }
            return x;
        }
        """,
        3,  # expected 3 from test
    )


if __name__ == "__main__":
    main()
