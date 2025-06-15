from typing import List

from tree_sitter import Node


def get_source_text(node: Node) -> str:
    """Extract source text for a node"""
    return node.text.decode("utf-8") if node.text else ""


def get_calls(ast_node: Node) -> List[str]:
    """Extract function calls under an AST node."""
    calls = []
    if not ast_node:
        return calls

    # Stack for DFS traversal
    stack = [ast_node]

    while stack:
        current = stack.pop()

        if current.type == "call_expression":
            identifier = None
            for child in current.children:
                if child.type == "identifier":
                    # Assuming the function name is in an identifier node
                    assert identifier is None, (
                        "Multiple identifiers found in call expression"
                    )
                    identifier = get_source_text(child)
            if identifier:
                calls.append(identifier)

        # Add all children to the stack in reverse order
        # (to process them in the original left-to-right order)
        for child in reversed(current.children):
            stack.append(child)

    return calls


def get_definitions(ast_node: Node) -> List[str]:
    """Extract variable definitions under an AST node."""
    definitions = []
    if not ast_node:
        return definitions

    # Stack for DFS traversal
    stack = [ast_node]

    while stack:
        current = stack.pop()

        if current.type == "init_declarator":
            identifier = None
            for child in current.children:
                if child.type == "identifier":
                    identifier = child.text.decode()
                    break
            if identifier:
                definitions.append(identifier)
        elif current.type == "assignment_expression":
            identifier = None
            for child in current.children:
                if child.type == "identifier":
                    identifier = child.text.decode()
                    break
            if identifier:
                definitions.append(identifier)

        # Add all children to the stack in reverse order
        # (to process them in the original left-to-right order)
        for child in reversed(current.children):
            stack.append(child)

    return definitions
