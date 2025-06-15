from tree_sitter import Node


def get_source_text(node: Node) -> str:
    """Extract source text for a node"""
    return node.text.decode("utf-8") if node.text else ""
