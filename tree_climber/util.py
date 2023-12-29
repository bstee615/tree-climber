
import networkx as nx
from tree_sitter import Node


def concretize_graph(G):
    """Convert all data in a graph to serializable types."""
    def to_id(n):
        return f"[{id(n)}] {n}"
    mapping = {n: to_id(n) for n in G.nodes()}
    attrs = {to_id(n): n.asdict() for n in G.nodes()}
    labels = {to_id(n): str(n) for n in G.nodes()}
    # Relabel nodes to a unique string ID
    G = nx.relabel_nodes(G, mapping, copy=True)
    # Set node and edge attributes
    nx.set_node_attributes(G, attrs)
    nx.set_node_attributes(G, labels, name="label")
    return G


def concretize_node(node):
    """Convert all data in an AST-based node to serializable types."""
    if isinstance(node, Node):
        return {
            "type": node.type,
            "start_point": node.start_point,
            "end_point": node.end_point,
            "text": node.text.decode(),
        }
    else:
        return node
