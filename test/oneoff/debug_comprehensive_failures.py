#!/usr/bin/env python3
"""
Debug script for comprehensive test failures.
Created: 2025-08-14

Context: After running the comprehensive C CFG test suite, 11 out of 37 tests failed.
Need to categorize failures into:
1. Implementation bugs in the CFG visitor
2. Incorrect test expectations
3. Missing functionality

Problem: Multiple failure types identified:
- Switch statements: CASE nodes being removed by post-processing
- Function definitions: Parameter extraction issues
- Node counts: Some tests have incorrect expectations
- For loops: Node type/count mismatches

Investigation: Systematically analyze each failure category to determine
root causes and distinguish between code bugs vs. test bugs.
"""

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.cfg_types import NodeType


def analyze_failure(test_name, code, expected_issues=None):
    """Analyze a specific test case and its CFG output."""
    print(f"\n{'=' * 60}")
    print(f"ANALYZING: {test_name}")
    print(f"{'=' * 60}")

    builder = CFGBuilder("c")
    builder.setup_parser()

    cfg = builder.build_cfg(code)

    # Count node types
    node_type_counts = {}
    for node in cfg.nodes.values():
        node_type = node.node_type
        node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    print("Node type distribution:")
    for node_type, count in node_type_counts.items():
        print(f"  {node_type.name}: {count}")

    print(f"\nTotal nodes: {len(cfg.nodes)}")

    if expected_issues:
        print(f"\nExpected issues: {expected_issues}")

    print("\nDetailed node analysis:")
    for node_id, node in sorted(cfg.nodes.items()):
        metadata_summary = ""
        if node.metadata:
            calls = len(node.metadata.function_calls)
            defs = len(node.metadata.variable_definitions)
            uses = len(node.metadata.variable_uses)
            if calls or defs or uses:
                metadata_summary = f" [calls:{calls}, defs:{defs}, uses:{uses}]"

        print(
            f"  Node {node_id}: {node.node_type.name} - '{node.source_text}' - "
            f"successors: {list(node.successors)}{metadata_summary}"
        )


def main():
    """Run analysis on known failing test cases."""

    # 1. Switch statement issue (CASE nodes removed)
    analyze_failure(
        "Switch with breaks",
        """
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
        """,
        ["Expected 3 CASE nodes, getting 0 - post-processing removes them"],
    )

    # 2. Function definition parameter issue
    analyze_failure(
        "Function definition parameters",
        """
        int test_func(int a, int b) {
            return a + b;
        }
        """,
        ["Expected parameters [a, b], getting ['(']"],
    )

    # 3. If-only statement node count
    analyze_failure(
        "If-only node count",
        """
        int main() {
            int x = 5;
            if (x > 0) {
                x = x + 1;
            }
            return x;
        }
        """,
        ["Test expects 1 STATEMENT but declares it twice, may need 2"],
    )

    # 4. For loop structure
    analyze_failure(
        "For loop structure",
        """
        int main() {
            int sum = 0;
            for (int i = 0; i < 10; i++) {
                sum = sum + i;
            }
            return sum;
        }
        """,
        ["Need to verify for loop node count expectations"],
    )

    # 5. Empty function case
    analyze_failure(
        "Empty function",
        """
        void empty_func() {
        }
        """,
        ["Test expects 2 nodes (entry + exit), check actual count"],
    )


if __name__ == "__main__":
    main()
