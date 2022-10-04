"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

import networkx as nx


def make_cpg(ast, cfg, duc):
    ast = ast.copy()
    cfg = cfg.copy()
    duc = duc.copy()
    nx.set_edge_attributes(
        ast, {(u, v): {"graph_type": "AST", "color": "black"} for u, v in ast.edges()}
    )
    nx.set_edge_attributes(
        cfg,
        {
            (u, v, k): {"graph_type": "CFG", "color": "green"}
            for u, v, k in cfg.edges(keys=True)
        },
    )
    nx.set_edge_attributes(
        duc, {(u, v): {"graph_type": "DUC", "color": "red"} for u, v in duc.edges()}
    )
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

    # NOTE: see issue https://github.com/pydot/pydot/issues/264.
    # when using pyvis, we don't need to do this and I think it's handled elsewhere -
    # keeping it here for posterity.
    # labels = {
    #     n: {"label": l.replace(":", "_")}
    #     for n, l in nx.get_node_attributes(cpg, "label").items()
    # }
    # nx.set_node_attributes(cpg, labels)

    return cpg
