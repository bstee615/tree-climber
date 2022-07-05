"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

from matplotlib import pyplot as plt
from tests.utils import *
from treehouse.globals import example_c
from treehouse.ast_creator import ASTCreator
from treehouse.dataflow.def_use import make_duc
from treehouse.tree_sitter_utils import c_parser
from treehouse.cfg_creator import CFGCreator

import networkx as nx

def get_cpg(ast, cfg, duc):
    ast = ast.copy()
    cfg = cfg.copy()
    duc = duc.copy()
    nx.set_edge_attributes(ast, {(u, v): "AST" for u, v in ast.edges()}, "graph_type")
    nx.set_edge_attributes(cfg, {(u, v, k): "CFG" for u, v, k in cfg.edges(keys=True)}, "graph_type")
    nx.set_edge_attributes(duc, {(u, v): "DUC" for u, v in duc.edges()}, "graph_type")
    max_ast_node = max(ast.nodes())
    cfg = nx.relabel_nodes(cfg, {n: attr.get("ast_node", max_ast_node+n+1) for n, attr in cfg.nodes(data=True)})
    duc = nx.relabel_nodes(duc, {n: attr.get("ast_node") for n, attr in duc.nodes(data=True)})
    cpg = nx.MultiDiGraph(ast)
    cpg = nx.compose(cpg, cfg)
    cpg = nx.compose(cpg, nx.MultiDiGraph(duc))

    # cpg.add_nodes_from(ast.nodes(data=True))
    # cpg.add_edges_from([(u, v, dict(graph_type="AST", **attr)) for (u, v, attr) in ast.edges(data=True)])
    
    # max_ast_node = max(ast.nodes())
    # ast_cfg_map = {n:max_ast_node+n for n in [n for n, attr in cfg.nodes(data=True) if attr["ast_node"] is None]}
    # cfg = nx.relabel_nodes(cfg, ast_cfg_map)
    # for cpg_id in ast_cfg_map.values():
    #     cfg.nodes[cpg_id]["ast_node"] = cpg_id
    # cpg.add_nodes_from([(n, attr) for n, attr in cfg.nodes(data=True) if n not in cpg])
    # cpg.add_edges_from([(cfg.nodes[u]["ast_node"], cfg.nodes[v]["ast_node"], k, dict(graph_type="CFG", **attr)) for (u, v, k, attr) in cfg.edges(keys=True, data=True)])

    # cfg_ast_map = {n: attr["ast_node"] for n, attr in cfg.nodes(data=True)}
    # cpg.add_edges_from([(cfg_ast_map[u], cfg_ast_map[v], dict(graph_type="DUC", **attr)) for (u, v, attr) in duc.edges(data=True)])

    return cpg

def test():
    code = example_c.read_text()
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)
    cpg = get_cpg(ast, cfg, duc)

    pos = nx.nx_pydot.graphviz_layout(cpg, prog="dot")
    nx.draw(cpg, pos=pos)
    nx.draw_networkx_labels(cpg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cpg.nodes(data=True)})
    for graph_type, color in {
        "AST": "black",
        "CFG": "blue",
        "DUC": "red",
    }.items():
        nx.draw_networkx_edges(cpg, pos=pos, edge_color=color, edgelist=[(u, v) for u, v, k, attr in cpg.edges(keys=True, data=True) if attr["graph_type"] == graph_type])
    nx.draw_networkx_edge_labels(cpg, pos=pos, edge_labels={(u, v): attr.get("label", "") for u, v, k, attr in cpg.edges(keys=True, data=True)})
    plt.show()
