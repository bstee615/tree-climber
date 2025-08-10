from typing import override

import pygraphviz as pgv
from tree_sitter import Node

from tree_sprawler.cli.visualizers.base_visualizer import (
    BaseVisualizer,
    get_node_display,
    get_node_label,
    truncate_ast_label,
)

from .constants import (
    AST_OVERLAY_BORDER_COLOR,
    AST_OVERLAY_EDGE_COLOR,
    AST_OVERLAY_FONT_SIZE,
    AST_OVERLAY_NODE_COLOR,
    AST_OVERLAY_SHOW_ONLY_NAMED,
    DEFAULT_DPI,
)


class BiGraphVisualizer(BaseVisualizer):
    @override
    def visualize(self):
        ast_root, cfg, duc_edges = self.ast_root, self.cfg, self.duc_edges

        # 1) Build AST-only graph first (tree layout with straight lines)
        G_ast = pgv.AGraph(strict=False, directed=True)
        G_ast.graph_attr.update(
            ranksep="0.15",
            nodesep="0.1",
            dpi=str(DEFAULT_DPI),
            rankdir="TB",
            ordering="out",
            splines=True,
        )
        G_ast.node_attr.update(style="filled")
        G_ast.edge_attr.update(
            arrowhead="none",
            tailport="s",
            headport="n",
            penwidth="1",
            color=AST_OVERLAY_EDGE_COLOR,
        )

        def ast_label(ts_node) -> str:
            node_type = getattr(ts_node, "type", str(ts_node))
            text = getattr(ts_node, "text", b"") or b""
            try:
                text_str = text.decode("utf-8").strip().replace("\n", " ")
            except Exception:
                text_str = ""
            return truncate_ast_label(
                f"{node_type}: {text_str}" if text_str else node_type
            )

        def add_ast(ts_node):
            nid = f"ast_{ts_node.id}"
            if not G_ast.has_node(nid):
                G_ast.add_node(
                    nid,
                    label=ast_label(ts_node),
                    shape="box",
                    fontsize=str(AST_OVERLAY_FONT_SIZE),
                    fillcolor=AST_OVERLAY_NODE_COLOR,
                    color=AST_OVERLAY_BORDER_COLOR,
                )
            children = [
                c
                for c in getattr(ts_node, "children", [])
                if (not AST_OVERLAY_SHOW_ONLY_NAMED or getattr(c, "is_named", False))
            ]
            for c in children:
                cid = f"ast_{c.id}"
                if not G_ast.has_node(cid):
                    G_ast.add_node(
                        cid,
                        label=ast_label(c),
                        shape="box",
                        fontsize=str(AST_OVERLAY_FONT_SIZE),
                        fillcolor=AST_OVERLAY_NODE_COLOR,
                        color=AST_OVERLAY_BORDER_COLOR,
                    )
                G_ast.add_edge(nid, cid)
                add_ast(c)

        ast_root_node = getattr(ast_root, "root_node", None)
        if ast_root_node is not None:
            add_ast(ast_root_node)
            # Keep the root at the top rank
            G_ast.add_subgraph(
                [f"ast_{ast_root_node.id}"], name="rank_ast_root"
            ).graph_attr.update(rank="min")

        # 2) Build combined graph: draw AST first, then CFG/DFG; align CFG node y to AST root via rank=same
        G = pgv.AGraph(strict=False, directed=True)
        G.graph_attr.update(
            ranksep="0.2",
            nodesep="0.45",
            dpi=str(DEFAULT_DPI),
            rankdir="TB",
            splines=True,
        )
        G.node_attr.update(style="filled")

        # Helper to add AST into any target graph with the same styling
        def add_ast_into(graph: pgv.AGraph, ts_node: Node):
            nid = f"ast_{ts_node.id}"
            if not graph.has_node(nid):
                graph.add_node(
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
                for c in getattr(ts_node, "children", [])
                if (not AST_OVERLAY_SHOW_ONLY_NAMED or getattr(c, "is_named", False))
            ]
            for c in children:
                cid = f"ast_{c.id}"
                if not graph.has_node(cid):
                    graph.add_node(
                        cid,
                        label=ast_label(c),
                        shape="box",
                        fontsize=str(AST_OVERLAY_FONT_SIZE),
                        fillcolor=AST_OVERLAY_NODE_COLOR,
                        color=AST_OVERLAY_BORDER_COLOR,
                        style="filled",
                    )
                # AST edges should be straight and non-arrowed to look like a tree
                graph.add_edge(
                    nid,
                    cid,
                    arrowhead="none",
                    tailport="s",
                    headport="n",
                    color=AST_OVERLAY_EDGE_COLOR,
                )
                add_ast_into(graph, c)

        # Rebuild AST inside the combined graph
        if ast_root_node is not None:
            add_ast_into(G, ast_root_node)

        # Add CFG nodes and align with AST roots
        for node_id, node in cfg.nodes.items():
            color, shape = get_node_display(node)
            node_label = get_node_label(node)
            G.add_node(node_id, label=node_label, shape=shape, fillcolor=color)
            ts_node = getattr(node, "ast_node", None)
            if ts_node is not None:
                ast_nid = f"ast_{ts_node.id}"
                if G.has_node(ast_nid):
                    # Align ranks (y) between CFG node and its AST root
                    G.add_subgraph(
                        [node_id, ast_nid], name=f"rank_pair_{node_id}"
                    ).graph_attr.update(rank="same")
                    # Visual dotted link
                    G.add_edge(
                        node_id,
                        ast_nid,
                        style="dotted",
                        color=AST_OVERLAY_EDGE_COLOR,
                        arrowhead="none",
                        penwidth="1",
                        headlabel=node_label,
                        labelfontsize=str(AST_OVERLAY_FONT_SIZE),
                    )

        # Add CFG/DFG edges after nodes
        for node_id, node in cfg.nodes.items():
            for succ in node.successors:
                label = node.edge_labels.get(succ, "")
                G.add_edge(node_id, succ, color="black", label=label)
                if (node_id, succ) in duc_edges:
                    dfg_label = ", ".join(sorted(duc_edges[(node_id, succ)]))
                    G.add_edge(
                        node_id,
                        succ,
                        color="red",
                        style="dashed",
                        fontcolor="red",
                        label=dfg_label,
                    )

        # Draw AST-only (dot tree)
        G_ast.draw(str(self.output_path("ast")), prog="dot")
        print(f"Saved AST visualization: {self.output_path('ast')}")

        # Draw CFG/DFG-only (dot)
        G_cfg = pgv.AGraph(strict=False, directed=True)
        G_cfg.graph_attr.update(
            ranksep="0.2",
            nodesep="0.45",
            dpi=str(DEFAULT_DPI),
            rankdir="TB",
            splines=True,
        )
        G_cfg.node_attr.update(style="filled")
        for node_id, node in cfg.nodes.items():
            col, shape = get_node_display(node)
            G_cfg.add_node(
                node_id, label=get_node_label(node), shape=shape, fillcolor=col
            )
        for node_id, node in cfg.nodes.items():
            for succ in node.successors:
                lab = node.edge_labels.get(succ, "")
                G_cfg.add_edge(node_id, succ, color="black", label=lab)
                if (node_id, succ) in duc_edges:
                    dfg_label = ", ".join(sorted(duc_edges[(node_id, succ)]))
                    G_cfg.add_edge(
                        node_id,
                        succ,
                        color="red",
                        style="dashed",
                        fontcolor="red",
                        label=dfg_label,
                    )
        G_cfg.draw(str(self.output_path("cfg")), prog="dot")
        print(f"Saved CFG/DFG visualization: {self.output_path('cfg')}")

        # Draw combined
        G.draw(str(self.output_path("cpg")), prog="dot")
        print(f"Saved CPG visualization: {self.output_path('cpg')}")
