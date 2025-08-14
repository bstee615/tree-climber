#!/usr/bin/env python3
"""
Debug script for switch statement CFG generation issue.
Created: 2025-08-14

Context: Running comprehensive C CFG tests, discovered that switch statements
are not generating expected CASE nodes. The test expects 3 CASE nodes for:
case 1, case 2, and default, but getting 0 CASE nodes.

Problem: Need to understand why visit_case_statement is not being called
during CFG generation for switch statements. This could be due to:
1. AST structure not matching expected node types
2. Visitor method not properly registered/dispatched
3. Case statement nodes not being recognized in compound_statement traversal

Investigation: Check AST structure and visitor method dispatch for case statements.
"""

from tree_climber.ast_utils import parse_source_to_ast
from tree_climber.cfg.builder import CFGBuilder


def print_ast_structure(node, indent=0):
    """Print the AST structure to understand how switch/case is parsed"""
    prefix = "  " * indent
    print(f"{prefix}{node.type}")

    if hasattr(node, "children"):
        for child in node.children:
            if child.is_named:
                print_ast_structure(child, indent + 1)


def debug_switch_ast():
    code = """
    int main() {
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

    tree = parse_source_to_ast(code, "c")
    print("AST Structure:")
    print_ast_structure(tree.root_node)

    print("\n" + "=" * 50)
    print("Now let's see what the CFG visitor does...")

    builder = CFGBuilder("c")
    builder.setup_parser()

    # Get the visitor to debug
    from tree_climber.cfg.languages.c import CCFGVisitor

    visitor = CCFGVisitor()

    # Check if the visitor has handlers for case statements
    print(
        f"Has visit_case_statement method: {hasattr(visitor, 'visit_case_statement')}"
    )
    print(
        f"Has visit_switch_statement method: {hasattr(visitor, 'visit_switch_statement')}"
    )

    # Check what handles_type returns for various node types
    print("\nNode type handling:")
    test_types = [
        "switch_statement",
        "case_statement",
        "compound_statement",
        "default",
        "labeled_statement",
    ]
    for node_type in test_types:
        handles = getattr(visitor, "handles_type", lambda x: False)(node_type)
        print(f"  {node_type}: {handles}")


if __name__ == "__main__":
    debug_switch_ast()
