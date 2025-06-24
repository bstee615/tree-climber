from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from tree_sitter import Node, Tree


def get_source_text(node: Node) -> str:
    """Extract source text for a node"""
    return node.text.decode("utf-8") if node.text else ""


@dataclass
class ProgramPoint:
    """Data class representing a program point with row and column."""

    row: int
    column: int


@dataclass
class ASTNode:
    """Data class representing an AST node with its properties."""

    id: int
    node_type: str
    start_point: ProgramPoint
    end_point: ProgramPoint
    start_byte: int
    end_byte: int
    text: str
    is_named: bool
    children: List["ASTNode"]


def ast_node_to_dict(node: Node) -> ASTNode:
    children = []

    for child in node.children:
        children.append(ast_node_to_dict(child))

    return ASTNode(
        id=node.id,
        node_type=node.type,
        start_point=ProgramPoint(row=node.start_point[0], column=node.start_point[1]),
        end_point=ProgramPoint(row=node.end_point[0], column=node.end_point[1]),
        start_byte=node.start_byte,
        end_byte=node.end_byte,
        text=get_source_text(node),
        is_named=node.is_named,
        children=children,
    )


def find_nodes_containing_position(
    node: Node, row: int, column: int, results: Optional[List[Node]] = None
) -> List[Node]:
    """Find all AST nodes that contain the given cursor position.

    Args:
        node: Root AST node to search from
        row: 0-based row number of cursor position
        column: 0-based column number of cursor position
        results: List to accumulate results (used for recursion)

    Returns:
        List of AST nodes that contain the cursor position, ordered from root to leaf
    """
    if results is None:
        results = []

    # Check if position is within this node
    start_row, start_col = node.start_point
    end_row, end_col = node.end_point

    # Position is contained if:
    # - It's after the start point and before the end point
    if (row > start_row or (row == start_row and column >= start_col)) and (
        row < end_row or (row == end_row and column <= end_col)
    ):
        results.append(node)

        # Recursively check children
        for child in node.children:
            find_nodes_containing_position(child, row, column, results)

    return results


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
