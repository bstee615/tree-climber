from typing import Callable, List, Optional

from tree_sitter import Node


def get_source_text(node: Node) -> str:
    """Extract source text for a node"""
    return node.text.decode("utf-8") if node.text else ""


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
