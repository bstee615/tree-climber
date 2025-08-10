from typing import override

import pygraphviz as pgv
from tree_sitter import Node

from tree_sprawler.cli.visualizers.base_visualizer import (
    BaseVisualizer,
    get_node_display,
    get_node_label,
)
from tree_sprawler.cli.visualizers.utils import ast_label

from .constants import (
    AST_OVERLAY_BORDER_COLOR,
    AST_OVERLAY_EDGE_COLOR,
    AST_OVERLAY_FONT_SIZE,
    AST_OVERLAY_LINKING_EDGE_COLOR,
    AST_OVERLAY_NODE_COLOR,
    AST_OVERLAY_SHOW_ONLY_NAMED,
    DEFAULT_DPI,
)


class BiGraphVisualizer(BaseVisualizer):
    @override
    def visualize(self):
        options = self.options
        ast_root = self.ast_root
        cfg = self.cfg
        duc_edges = self.duc_edges

        # Combined CPG graph (AST + CFG + optional DFG overlay)
        if not options.draw_cpg:
            return
        if ast_root is None:
            raise ValueError("AST required to draw CPG")
        if cfg is None:
            raise ValueError("CFG required to draw CPG")
        G = pgv.AGraph(strict=False, directed=True)
        G.graph_attr.update(
            ranksep="0.2",
            nodesep="0.45",
            dpi=str(DEFAULT_DPI),
            rankdir="TB",
            splines=True,
            margin="0.05",
            bgcolor="white",
        )
        G.node_attr.update(style="filled")

        def add_ast_into(ts_node: Node):
            nid = f"ast_{ts_node.id}"
            if not G.has_node(nid):
                G.add_node(
                    nid,
                    label=ast_label(ts_node),
                    shape="box",
                    fontsize=str(AST_OVERLAY_FONT_SIZE),
                    fillcolor=AST_OVERLAY_NODE_COLOR,
                    color=AST_OVERLAY_BORDER_COLOR,
                    style="filled",
                )
            children = [
                c
                for c in ts_node.children
                if (not AST_OVERLAY_SHOW_ONLY_NAMED or c.is_named)
            ]
            for c in children:
                cid = f"ast_{c.id}"
                if not G.has_node(cid):
                    G.add_node(
                        cid,
                        label=ast_label(c),
                        shape="box",
                        fontsize=str(AST_OVERLAY_FONT_SIZE),
                        fillcolor=AST_OVERLAY_NODE_COLOR,
                        color=AST_OVERLAY_BORDER_COLOR,
                        style="filled",
                    )
                G.add_edge(
                    nid,
                    cid,
                    arrowhead="none",
                    tailport="s",
                    headport="n",
                    color=AST_OVERLAY_EDGE_COLOR,
                )
                add_ast_into(c)

        add_ast_into(ast_root.root_node)

        # Add CFG nodes and link each to its AST node if available
        for node_id, node in cfg.nodes.items():
            color, shape = get_node_display(node)
            node_label = get_node_label(node)
            G.add_node(node_id, label=node_label, shape=shape, fillcolor=color)
            ts_node = node.ast_node
            if ts_node is not None:
                ast_nid = f"ast_{ts_node.id}"
                if G.has_node(ast_nid):
                    G.add_subgraph(
                        [node_id, ast_nid], name=f"rank_pair_{node_id}"
                    ).graph_attr.update(rank="same")
                    G.add_edge(
                        node_id,
                        ast_nid,
                        style="dotted",
                        color=AST_OVERLAY_LINKING_EDGE_COLOR,
                        arrowhead="none",
                        penwidth="1",
                        headlabel=node_label,
                        labelfontsize=str(AST_OVERLAY_FONT_SIZE),
                        labelfontcolor=AST_OVERLAY_LINKING_EDGE_COLOR,
                    )

        # Add CFG edges and optional DFG overlay
        for node_id, node in cfg.nodes.items():
            for succ in node.successors:
                label = node.edge_labels.get(succ, "")
                G.add_edge(node_id, succ, color="black", label=label)
                if (
                    options.draw_dfg
                    and duc_edges is not None
                    and (node_id, succ) in duc_edges
                ):
                    dfg_label = ", ".join(sorted(duc_edges[(node_id, succ)]))
                    G.add_edge(
                        node_id,
                        succ,
                        color="red",
                        style="dashed",
                        fontcolor="red",
                        label=dfg_label,
                    )

        G.draw(str(self.output_path("cpg")), prog="dot")
        print(f"Saved CPG visualization: {self.output_path('cpg')}")
