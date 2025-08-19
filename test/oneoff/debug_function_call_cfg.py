"""
Debug function call CFG behavior - Created 2025-08-14

This script examines how function calls are currently handled in CFG generation
to understand what needs to be fixed for the first parsing bug:
"Both languages CFG, Function calls should have an edge from exit going back to the call"
"""

import os
import tempfile

from tree_sitter_language_pack import get_parser

from tree_climber.cfg.languages.c import CCFGVisitor
from tree_climber.cfg.languages.java import JavaCFGVisitor

# Simple Java test with function call
java_code = """
public class Test {
    public static void helper() {
        System.out.println("helper");
    }
    
    public static void main() {
        int x = 5;
        helper();  // Function call
        x = x + 1;
    }
}
"""

# Simple C test with function call
c_code = """
void helper() {
    printf("helper");
}

int main() {
    int x = 5;
    helper();  // Function call
    x = x + 1;
    return x;
}
"""


def analyze_cfg(language, code, visitor_class):
    print(f"\n=== {language.upper()} CFG Analysis ===")

    # Parse code
    parser = get_parser(language)
    tree = parser.parse(bytes(code, "utf8"))

    # Generate CFG
    visitor = visitor_class()
    visitor.visit(tree.root_node)
    visitor.postprocess_cfg()

    cfg = visitor.cfg
    print(f"Function: {cfg.function_name}")
    print(f"Total nodes: {len(cfg.nodes)}")
    print(f"Entry nodes: {cfg.entry_node_ids}")
    print(f"Exit nodes: {cfg.exit_node_ids}")

    # Print all nodes and their connections
    print("\nNodes:")
    for node_id, node in sorted(cfg.nodes.items()):
        print(f"  {node_id}: {node.node_type} - '{node.source_text.strip()}'")
        if node.successors:
            print(f"    -> {list(node.successors)}")
        if node.predecessors:
            print(f"    <- {list(node.predecessors)}")
        if node.metadata.function_calls:
            print(f"    Calls: {node.metadata.function_calls}")


if __name__ == "__main__":
    analyze_cfg("java", java_code, JavaCFGVisitor)
    analyze_cfg("c", c_code, CCFGVisitor)
