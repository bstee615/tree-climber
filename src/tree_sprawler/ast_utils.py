from typing import Callable, List, Optional

from tree_sitter import Node


def get_source_text(node: Node) -> str:
    """Extract source text for a node"""
    return node.text.decode("utf-8") if node.text else ""


def get_child_by_field_name(node: Node, *field_names: str) -> Optional[Node]:
    """Get the first child node with the specified field name."""
    child = None
    for part in field_names:
        child = node.child_by_field_name(part)
        if child is None:
            break
        node = child
    return child


def get_required_child_by_field_name(node: Node, *field_names: str) -> Node:
    """Get the first child node with the specified field name."""
    child = get_child_by_field_name(node, *field_names)
    if child is None:
        raise ValueError(f"Child with field names '{'.'.join(field_names)}' not found")
    return child


def get_child_by_type(node: Node, *field_names: str) -> Optional[Node]:
    """Get the first child node with the specified field name."""
    child = None
    for part in field_names:
        for current_child in node.children:
            if current_child.type == part:
                child = current_child
        if child is None:
            break
        node = child
    return child


def get_required_child_by_type(node: Node, *field_names: str) -> Node:
    """Get the first child node with the specified field name."""
    child = get_child_by_type(node, *field_names)
    if child is None:
        raise ValueError(f"Child with type '{'.'.join(field_names)}' not found")
    return child


def dfs(ast_node: Node, callback: Callable[[Node], Optional[str]]) -> List[str]:
    """Generic DFS traversal with a callback for AST node processing."""
    results = []
    if not ast_node:
        return results

    stack = [ast_node]
    while stack:
        current = stack.pop()

        result = callback(current)
        if result is not None:
            results.append(result)

        # Add children in reverse order for left-to-right traversal
        for child in reversed(current.children):
            stack.append(child)

    return results
