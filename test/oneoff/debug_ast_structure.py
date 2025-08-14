#!/usr/bin/env python3
"""
Debug script for AST structure of nested switch.
Created: 2025-08-14

Context: Check if the default case in the outer switch is being properly
parsed and visited by examining the AST structure.

Investigation: Walk through the AST to understand the switch statement structure.
"""

from tree_climber.ast_utils import parse_source_to_ast, get_source_text


def print_ast_structure(node, indent=0, max_depth=15):
    """Print AST structure with limited depth."""
    if indent > max_depth:
        return

    prefix = "  " * indent
    print(
        f"{prefix}{node.type}: '{get_source_text(node)[:50]}{'...' if len(get_source_text(node)) > 50 else ''}'"
    )

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
                if indent < 4:  # Only recurse a few levels
                    print_ast_structure(child, indent + 2, max_depth)


def debug_nested_switch_ast():
    """Debug the AST structure of nested switch."""

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

    tree = parse_source_to_ast(code, "c")

    print("\nAST Structure:")
    print_ast_structure(tree.root_node)

    # Find the switch statements specifically
    def find_switches(node, switches=[]):
        if node.type == "switch_statement":
            switches.append(node)
        for child in node.children:
            if child.is_named:
                find_switches(child, switches)
        return switches

    switches = find_switches(tree.root_node, [])
    print(f"\nFound {len(switches)} switch statements:")

    for i, switch_node in enumerate(switches):
        print(f"\nSwitch {i + 1}:")
        print(f"  Full text: '{get_source_text(switch_node)}'")

        # Find the body of this switch
        for child in switch_node.children:
            if child.type == "compound_statement":
                print(f"  Switch body: '{get_source_text(child)[:100]}...'")

                # Look for case statements in the body
                case_count = 0
                default_count = 0
                for body_child in child.children:
                    if body_child.type == "case_statement":
                        case_text = get_source_text(body_child)[:50]
                        print(f"    Case: '{case_text}...'")
                        case_count += 1

                        # Check if this is a default case
                        for case_child in body_child.children:
                            if case_child.type == "default":
                                print(f"      -> DEFAULT case found!")
                                default_count += 1

                print(f"  Total cases: {case_count}, defaults: {default_count}")


if __name__ == "__main__":
    debug_nested_switch_ast()
