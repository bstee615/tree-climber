"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

import networkx as nx

from tree_climber.utils import get_method_definition, get_method_reference
from tree_climber.utils import subgraph
from tree_climber.ast import make_ast, make_ast_from_tree
from tree_climber.cfg import make_cfg
from tree_climber.dataflow.def_use import make_duc
from tree_climber.utils import c_parser


def assemble_cpg(ast, cfg, duc):
    """
    Assemble the CPG.
    """
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


def make_code_cpg(code, draw_ast=False, draw_cfg=False, draw_duc=False):
    """
    Parse one file into a CPG.
    """
    tree = c_parser.parse(bytes(code, encoding="utf-8"))
    ast = make_ast_from_tree(tree)
    if draw_ast:
        draw_ast(ast)

    cfg = make_cfg(ast)
    if draw_cfg:
        draw_cfg(cfg)
    print("successfully parsed code")

    duc = make_duc(ast, cfg)
    if draw_duc:
        draw_duc(duc)

    cpg = assemble_cpg(ast, cfg, duc)

    return cpg


def make_file_cpg(filename, draw_ast=False, draw_cfg=False, draw_duc=False):
    """
    Parse one file into a CPG.
    """
    ast = make_ast(filename)
    if draw_ast:
        draw_ast(ast)

    cfg = make_cfg(ast)
    if draw_cfg:
        draw_cfg(cfg)
    print("successfully parsed", filename)

    duc = make_duc(ast, cfg)
    if draw_duc:
        draw_duc(duc)

    cpg = assemble_cpg(ast, cfg, duc)

    return cpg


def make_cpg(filenames):
    """
    Parse a list of files into a combined CPG.
    """
    cpgs = []
    for filename in filenames:
        file_cpg = make_file_cpg(filename)
        cpgs.append(file_cpg)
    combined_cpg = stitch_cpg(cpgs)
    return combined_cpg


def stitch_cpg(cpgs):
    """
    Stitch together multiple CPGs.
    """
    combined_cpg = None
    # merge into one big CPG
    stitch_order = cpgs
    running_offset = 0
    for i in range(len(stitch_order)):
        stitch_order[i] = nx.convert_node_labels_to_integers(
            stitch_order[i], first_label=running_offset
        )
        running_offset += stitch_order[i].number_of_nodes()
    combined_cpg = nx.compose_all(cpgs)

    combined_ast = subgraph(combined_cpg, {"AST"})

    method_refs = [
        get_method_reference(n, typ, combined_ast)
        for n, typ in combined_cpg.nodes(data="type")
    ]
    method_refs = [n for n in method_refs if n is not None]

    method_defs = [
        get_method_definition(n, typ, combined_ast)
        for n, typ in combined_cpg.nodes(data="type")
    ]
    method_defs = [n for n in method_defs if n is not None]

    call_graph_edges = []
    methodname_to_defnode = {methodname: n for n, methodname in method_defs}
    for methodnode, methodname in method_refs:
        if methodname in methodname_to_defnode:
            call_graph_edges.append((methodnode, methodname_to_defnode[methodname]))
        else:
            call_graph_edges.append(
                (methodnode, methodname)
            )  # TODO: handle it by adding a new well-defined placeholder node

    combined_cpg.add_edges_from(call_graph_edges, graph_type="CALL", color="purple")

    return combined_cpg
