#!/usr/bin/env python3
"""
Detailed AST analysis for parameter extraction.
Created: 2025-08-14

Context: Need to understand the exact AST structure of parameter_declaration
nodes to fix the parameter extraction logic.

Investigation: Walk through the parameter_list and parameter_declaration nodes
to understand how to correctly extract parameter names.
"""

from tree_climber.ast_utils import (
    get_child_by_field_name,
    get_required_child_by_field_name,
    get_source_text,
    parse_source_to_ast,
)


def walk_parameter_list(node, indent=0):
    """Walk through parameter list structure."""
    prefix = "  " * indent
    print(f"{prefix}{node.type}: '{get_source_text(node)}'")

    # Show named children
    for child in node.children:
        if child.is_named:
            walk_parameter_list(child, indent + 1)


def debug_parameter_structure():
    """Analyze parameter structure in detail."""

    code = """
    int test_func(int a, char *b, double c) {
        return a + c;
    }
    """

    tree = parse_source_to_ast(code, "c")

    # Navigate to the parameter list
    translation_unit = tree.root_node
    function_def = None
    for child in translation_unit.children:
        if child.type == "function_definition":
            function_def = child
            break

    if function_def:
        declarator = get_required_child_by_field_name(function_def, "declarator")
        parameter_list = get_required_child_by_field_name(declarator, "parameters")

        print("Parameter list analysis:")
        print(f"Parameter list type: {parameter_list.type}")
        print(f"Parameter list text: '{get_source_text(parameter_list)}'")
        print(f"Parameter list children count: {len(parameter_list.children)}")

        print("\nDetailed parameter list structure:")
        walk_parameter_list(parameter_list)

        print("\nExtracting parameters manually:")
        parameters = []
        for child in parameter_list.children:
            if child.type == "parameter_declaration":
                print(f"\nProcessing parameter_declaration: '{get_source_text(child)}'")

                # Try to find the declarator within the parameter
                declarator_child = get_child_by_field_name(child, "declarator")
                if declarator_child:
                    print(
                        f"  Found declarator: {declarator_child.type} - '{get_source_text(declarator_child)}'"
                    )

                    # For simple identifiers
                    if declarator_child.type == "identifier":
                        param_name = get_source_text(declarator_child)
                        parameters.append(param_name)
                        print(f"  Extracted identifier: '{param_name}'")

                    # For pointer declarators
                    elif declarator_child.type == "pointer_declarator":
                        # Need to find the identifier within the pointer declarator
                        for grandchild in declarator_child.children:
                            if grandchild.type == "identifier":
                                param_name = get_source_text(grandchild)
                                parameters.append(param_name)
                                print(f"  Extracted pointer identifier: '{param_name}'")
                                break
                else:
                    print(f"  No declarator field found in parameter_declaration")

        print(f"\nFinal extracted parameters: {parameters}")


if __name__ == "__main__":
    debug_parameter_structure()
