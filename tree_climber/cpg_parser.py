"""
Output CPG representation.
AST annotated with CFG, DUC edges.
"""

import networkx as nx

from tree_climber.base_parser import BaseParser
from tree_climber.ast_parser import ASTParser
from tree_climber.cfg_parser import CFGParser
from tree_climber.duc_parser import DUCParser


class CPGParser(BaseParser):
    @staticmethod
    def parse(data):
        ast = ASTParser.parse(data)
        cfg = CFGParser.parse(ast)
        duc = DUCParser.parse(cfg)

        nx.set_edge_attributes(ast, {(u, v): "AST" for u, v in ast.edges()}, "graph_type")
        nx.set_edge_attributes(cfg, {(u, v): "CFG" for u, v in cfg.edges()}, "graph_type")
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
        cpg = nx.compose(cpg, nx.MultiDiGraph(cfg))
        cpg = nx.compose(cpg, nx.MultiDiGraph(duc))

        labels = {n: {"label": l.replace(":", "_")} for n, l in nx.get_node_attributes(cpg, "label").items()}
        nx.set_node_attributes(cpg, labels)

        cpg.graph["graph_type"] = "CPG"
        cpg.graph["parents"] = {
            "AST": ast,
            "CFG": cfg,
            "DUC": duc,
        }

        return cpg

    @staticmethod
    def draw(cpg):
        from matplotlib import pyplot as plt
        for (n,d) in cpg.nodes(data=True):
            for k in list(d.keys()):
                if k != "label":
                    del d[k]
        pos = nx.nx_pydot.graphviz_layout(cpg, prog="dot")
        # TODO: remove AST subtrees without CFG/DUC edges
        nx.draw(cpg, pos=pos)
        nx.draw_networkx_labels(
            cpg,
            pos=pos,
            labels={
                n: attr.get("label", "<NO LABEL>")
                for n, attr in cpg.nodes(data=True)
            },
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

        import matplotlib.lines as mlines
        import matplotlib.pyplot as plt

        black_line = mlines.Line2D([], [], color='black', label='AST edge')
        blue_line = mlines.Line2D([], [], color='blue', label='CFG edge (condition)')
        red_line = mlines.Line2D([], [], color='red', label='DUC edge (variable name)')
        node = mlines.Line2D([], [], color="white", marker='o', markersize=10, markerfacecolor="#1F78B4", label='AST node')

        plt.legend(handles=[black_line, red_line, blue_line, node], title="Legend")

        plt.show()

# def test():
#     code = """int a = 30;

# struct foo {
#     int z;
# };

# int main()
# {
#     int x = 0;
#     for (int i = 0; i < 10; i ++) {
#         x -= i;
#     }
#     x += 20;
#     switch (x) {
#         case 0:
#             x += 30;
#             break;
#         case 1:
#             x -= 1;
#         case 2:
#             x -= a;
#             break;
#         default:
#             return -2;
#     }
#     while (x > 10) {
#         x -= 5;
#     }
#     do {
#         x -= 5;
#     } while (x > 0);
#     return x;
# }

# struct foo;
# """
#     from matplotlib import pyplot as plt

#     fig, ax = plt.subplots(2)
#     ast = ASTParser.parse(code)
#     pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog="dot")
#     nx.draw(
#         ast,
#         pos=pos,
#         labels={n: attr["label"] for n, attr in ast.nodes(data=True)},
#         with_labels=True,
#         ax=ax[0],
#     )

#     cfg = ASTParser.parse(ast)
#     pos = nx.drawing.nx_agraph.graphviz_layout(cfg, prog="dot")
#     nx.draw(
#         cfg,
#         pos=pos,
#         labels={n: attr["label"] for n, attr in cfg.nodes(data=True)},
#         with_labels=True,
#         ax=ax[1],
#     )
#     nx.draw_networkx_edge_labels(
#         cfg,
#         pos=pos,
#         edge_labels={
#             (u, v): attr.get("label", "") for (u, v, attr) in cfg.edges(data=True)
#         },
#         ax=ax[1],
#     )
#     plt.show()
