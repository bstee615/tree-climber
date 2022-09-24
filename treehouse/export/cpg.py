"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

import networkx as nx


def make_cpg(ast, cfg, duc):
    ast = ast.copy()
    cfg = cfg.copy()
    duc = duc.copy()
    nx.set_edge_attributes(ast, {(u, v): "AST" for u, v in ast.edges()}, "graph_type")
    nx.set_edge_attributes(
        cfg, {(u, v, k): "CFG" for u, v, k in cfg.edges(keys=True)}, "graph_type"
    )
    nx.set_edge_attributes(duc, {(u, v): "DUC" for u, v in duc.edges()}, "graph_type")
    max_ast_node = max(ast.nodes())
    cfg = nx.relabel_nodes(
        cfg,
        {
            n: attr.get("ast_node", max_ast_node + n + 1)
            for n, attr in cfg.nodes(data=True)
        },
    )
    duc = nx.relabel_nodes(
        duc, {n: attr.get("ast_node") for n, attr in duc.nodes(data=True)}
    )
    cpg = nx.MultiDiGraph(ast)
    cpg = nx.compose(cpg, cfg)
    cpg = nx.compose(cpg, nx.MultiDiGraph(duc))

    return cpg
