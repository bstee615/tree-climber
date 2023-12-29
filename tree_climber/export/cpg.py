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
EDGE_COLOR = {
    "CFG": DARK_RED,
    "AST": DARK_BLUE,
}


def make_cpg(ast, cfg, duc):
    ast_nodes = {node.ast_node.id: node for node in ast.nodes}
    nx.set_edge_attributes(ast, "AST", name="graph_source")
    nx.set_edge_attributes(cfg, "CFG", name="graph_source")

    # Combine AST and CFG
    cpg = nx.MultiDiGraph()
    cpg.add_nodes_from(ast.nodes(data=True))
    cpg.add_edges_from([(u, v, "AST", d) for u, v, d in ast.edges(data=True)])
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
        cpg.add_edge(u, v, key="CFG", **d)
    nx.set_node_attributes(cpg, node_colors, name="color")
    cpg = concretize_graph(cpg)

    # TODO add DUC pointing at CFG nodes

    return cpg


def visualize_cpg(cpg, fpath):
    """Visualize a CPG as an HTML file."""
    # Visualize
    net = Network(directed=True)
    net.from_nx(cpg)
    # Set node labels
    labels = nx.get_node_attributes(cpg, "label")
    for node in net.nodes:
        node["label"] = labels[node["id"]]
    # Set edge labels
    edge_labels = {(u, v, k): d.upper() for (u, v, k), d in nx.get_edge_attributes(cpg, "label").items()}
    edge_type = {}
    for u, v, k in cpg.edges(keys=True):
        id = (u, v)
        if id not in edge_type or edge_type[id] == "AST":
            edge_type[id] = k
    for edge in net.edges:
        id = (edge["from"], edge["to"])
        edge["color"] = EDGE_COLOR[edge_type[id]]
        edge["label"] = edge_labels.get((*id, "CFG"), None)
    # Export graph
    net.show(fpath, notebook=False)
