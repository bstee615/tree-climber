#!/usr/bin/env python3
"""
Debug script for parameter extraction issue.
Created: 2025-08-14

Context: Function parameter extraction only gets '['(']' instead of actual
parameter names like ['a', 'b']. The visit_function_definition method has
incorrect parameter parsing logic.

Problem: The parameter extraction loop has a 'break' statement that exits
after processing only the first parameter. Also need to understand the
correct AST structure for parameter_declaration nodes.

Investigation: Examine AST structure and fix parameter extraction logic.
"""

from tree_climber.ast_utils import get_source_text, parse_source_to_ast
from tree_climber.cfg.builder import CFGBuilder


def print_ast_structure(node, indent=0, max_depth=10):
    """Print AST structure with limited depth."""
    if indent > max_depth:
        return

    prefix = "  " * indent
    print(f"{prefix}{node.type}")

    # Show field names for better understanding
    if hasattr(node, "children"):
        for i, child in enumerate(node.children):
            if child.is_named:
                # Try to get field name
                field_name = ""
                if hasattr(node, "field_name_for_child"):
                    try:
                        field_name = node.field_name_for_child(i) or ""
                        if field_name:
                            field_name = f" [field: {field_name}]"
                    except:
                        pass

                print(f"{prefix}  └─ {child.type}{field_name}")
                if indent < 3:  # Only recurse a few levels
                    print_ast_structure(child, indent + 2, max_depth)


def debug_parameter_extraction():
    """Debug the parameter extraction issue."""

    code = """
    int test_func(int a, char *b, double c) {
        return a + c;
    }
    """

    print("Code being analyzed:")
    print(code)

    tree = parse_source_to_ast(code, "c")
    print("\nAST Structure:")
    print_ast_structure(tree.root_node)

    # Now test the current CFG extraction
    print("\n" + "=" * 60)
    print("Current CFG parameter extraction:")

    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    entry_nodes = [n for n in cfg.nodes.values() if n.node_type.name == "ENTRY"]
    if entry_nodes:
        entry_node = entry_nodes[0]
        print(f"Function name: {cfg.function_name}")
        print(f"Entry node text: '{entry_node.source_text}'")
        print(f"Variable definitions: {entry_node.metadata.variable_definitions}")
        print(f"Expected: ['a', 'b', 'c']")


if __name__ == "__main__":
    debug_parameter_extraction()
