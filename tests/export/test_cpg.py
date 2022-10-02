from tests.utils import *

from matplotlib import pyplot as plt
from tree_climber.globals import example_c
from tree_climber.ast_creator import ASTCreator
from tree_climber.dataflow.def_use import make_duc
from tree_climber.export.cpg import make_cpg
from tree_climber.tree_sitter_utils import c_parser
from tree_climber.cfg_creator import CFGCreator
import pytest


@pytest.mark.slow
def test_debug():
    code = example_c.read_text()
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)
    cpg = make_cpg(ast, cfg, duc)

    pos = nx.nx_pydot.graphviz_layout(cpg, prog="dot")
    nx.draw(cpg, pos=pos)
    nx.draw_networkx_labels(
        cpg,
        pos=pos,
        labels={n: attr.get("label", "<NO LABEL>") for n, attr in cpg.nodes(data=True)},
    )
    for graph_type, color in {
        "AST": "black",
        "CFG": "blue",
        "DUC": "red",
    }.items():
        nx.draw_networkx_edges(
            cpg,
            pos=pos,
            edge_color=color,
            edgelist=[
                (u, v)
                for u, v, k, attr in cpg.edges(keys=True, data=True)
                if attr["graph_type"] == graph_type
            ],
        )
    nx.draw_networkx_edge_labels(
        cpg,
        pos=pos,
        edge_labels={
            (u, v): attr.get("label", "")
            for u, v, k, attr in cpg.edges(keys=True, data=True)
        },
    )
    plt.show()
