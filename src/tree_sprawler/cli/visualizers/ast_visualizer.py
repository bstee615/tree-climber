from typing import override

import pygraphviz as pgv
from tree_sitter import Node

from tree_sprawler.cli.visualizers.base_visualizer import (
    BaseVisualizer,
)
from tree_sprawler.cli.visualizers.utils import ast_label

from .constants import (
    AST_OVERLAY_BORDER_COLOR,
    AST_OVERLAY_EDGE_COLOR,
    AST_OVERLAY_FONT_SIZE,
    AST_OVERLAY_NODE_COLOR,
    AST_OVERLAY_SHOW_ONLY_NAMED,
    DEFAULT_DPI,
)


class ASTVisualizer(BaseVisualizer):
    @override
    def visualize(self):
        options = self.options
        ast_root = self.ast_root
        if not options.draw_ast:
            return
        if ast_root is None:
            raise ValueError("AST root required to draw AST")
        G_ast = pgv.AGraph(strict=False, directed=True)
        G_ast.graph_attr.update(
            ranksep="0.5",
            nodesep="0.2",
            dpi=str(DEFAULT_DPI),
            splines="line",
        )
        G_ast.node_attr.update(style="filled")
        G_ast.edge_attr.update(
            arrowhead="none",
            tailport="s",
            headport="n",
            penwidth="1",
            color=AST_OVERLAY_EDGE_COLOR,
        )

        def add_ast_node(G: pgv.AGraph, ts_node: Node, nid: str):
            G.add_node(
                nid,
                label=ast_label(ts_node),
                shape="box",
                fontsize=str(AST_OVERLAY_FONT_SIZE),
                fillcolor=AST_OVERLAY_NODE_COLOR,
                color=AST_OVERLAY_BORDER_COLOR,
            )

        def add_ast(G: pgv.AGraph, ts_node: Node):
            nid = f"ast_{ts_node.id}"
            if not G.has_node(nid):
                add_ast_node(G, ts_node, nid)
            children = [
                c
                for c in ts_node.children
                if (not AST_OVERLAY_SHOW_ONLY_NAMED or c.is_named)
            ]
            for c in children:
                cid = f"ast_{c.id}"
                if not G.has_node(cid):
                    add_ast_node(G, c, cid)
                G.add_edge(nid, cid)
                add_ast(G, c)

        add_ast(G_ast, ast_root.root_node)
        G_ast.draw(str(self.output_path("ast")), prog="dot")
        print(f"Saved AST visualization: {self.output_path('ast')}")
