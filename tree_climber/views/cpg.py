"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

import networkx as nx
from tree_sitter import Node
from pyvis.network import Network
from ..util import concretize_graph


BLUE = "#5dade2"
DARK_BLUE = "#2874a6"
RED = "#FF5733"
DARK_RED = "#C70039"
DARK_GREEN = "#196f3d"
EDGE_COLOR = {
    "CFG": DARK_RED,
    "AST": DARK_BLUE,
    "DUC": DARK_GREEN,
}


def should_include(node):
    return node.is_named and node.type not in [
        "comment", "argument_list", "identifier", "number_literal", "string_literal",
    ]


def make_cpg(ast, cfg, duc):
    ast_nodes = {node.ast_node.id: node for node in ast.nodes}
    nx.set_edge_attributes(ast, "AST", name="graph_source")
    nx.set_edge_attributes(cfg, "CFG", name="graph_source")

    # Combine AST and CFG
    cpg = nx.MultiDiGraph()
    nodes_to_remove = []
    for n in ast.nodes():
        if not should_include(n.ast_node):
            nodes_to_remove.extend(nx.descendants(ast, n))
            nodes_to_remove.append(n)
    ast.remove_nodes_from(nodes_to_remove)
    cpg.add_nodes_from(ast.nodes(data=True))
    cpg.add_edges_from([(u, v, "AST", {"color": DARK_BLUE, **d}) for u, v, d in ast.edges(data=True)])
    # Default to AST node color
    node_colors = {n: {"background": BLUE, "border": DARK_BLUE, "highlight": {"background": BLUE, "border": DARK_BLUE}, "hover": {"background": BLUE, "border": DARK_BLUE}} for n in cpg.nodes(data=False)}
    for u, v, d in cfg.edges(data=True):
        if isinstance(u.ast_node, Node):
            u = ast_nodes[u.ast_node.id]
        else:
            cpg.add_node(u)
        if isinstance(v.ast_node, Node):
            v = ast_nodes[v.ast_node.id]
        else:
            cpg.add_node(v)
        # Set CFG node color
        node_colors[u] = {"background": RED, "border": DARK_RED, "highlight": {"background": RED, "border": DARK_RED}, "hover": {"background": RED, "border": DARK_RED}}
        node_colors[v] = {"background": RED, "border": DARK_RED, "highlight": {"background": RED, "border": DARK_RED}, "hover": {"background": RED, "border": DARK_RED}}
        cpg.add_edge(u, v, key="CFG", color=DARK_RED, **d)
        
    if duc is not None:
        for u, v, d in duc.edges(data=True):
            if isinstance(u.ast_node, Node):
                u = ast_nodes[u.ast_node.id]
            if isinstance(v.ast_node, Node):
                v = ast_nodes[v.ast_node.id]
            cpg.add_edge(u, v, key="DUC", color=DARK_GREEN, **d)

    nx.set_node_attributes(cpg, node_colors, name="color")
    cpg = concretize_graph(cpg)

    return cpg


def visualize_cpg(cpg, fpath):
    """Visualize a CPG as an HTML file."""
    # Visualize
    net = Network(directed=True)
    net.from_nx(cpg)
    net.show(fpath, notebook=False)
