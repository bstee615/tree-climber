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
    AST_OVERLAY_LINKING_EDGE_COLOR,
    AST_OVERLAY_NODE_COLOR,
    AST_OVERLAY_SHOW_ONLY_NAMED,
    DEFAULT_DPI,
)


class SubtreeVisualizer(BaseVisualizer):
    @override
    def visualize(self):
        options = self.options
        ast_root = self.ast_root
        cfg = self.cfg
        duc_edges = self.duc_edges

        def ast_label(ts_node: Node) -> str:
            node_type = ts_node.type if hasattr(ts_node, "type") else str(ts_node)
            text = getattr(ts_node, "text", b"") or b""
            try:
                text_str = text.decode("utf-8").strip().replace("\n", " ")
            except Exception:
                text_str = ""
            return truncate_ast_label(
                f"{node_type}: {text_str}" if text_str else node_type
            )

        # AST-only (full tree)
        if options.draw_ast:
            if ast_root is None:
                raise ValueError("AST root required to draw AST")
            G_ast = pgv.AGraph(strict=False, directed=True)
            G_ast.graph_attr.update(
                ranksep="0.15",
                nodesep="0.1",
                dpi=str(DEFAULT_DPI),
                rankdir="TB",
                ordering="out",
                splines=True,
                margin="0.05",
                bgcolor="white",
            )
            G_ast.node_attr.update(style="filled")
            G_ast.edge_attr.update(
                arrowhead="none",
                tailport="s",
                headport="n",
                penwidth="1",
                color=AST_OVERLAY_EDGE_COLOR,
            )

            def add_full_ast(ts_node: Node):
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
                    for c in ts_node.children
                    if (
                        not AST_OVERLAY_SHOW_ONLY_NAMED or getattr(c, "is_named", False)
                    )
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
                    add_full_ast(c)

            add_full_ast(ast_root.root_node)
            G_ast.add_subgraph(
                [f"ast_{ast_root.root_node.id}"], name="rank_ast_root"
            ).graph_attr.update(rank="min")
            G_ast.draw(str(self.output_path("ast")), prog="dot")
            print(f"Saved AST visualization: {self.output_path('ast')}")

        # CFG graph (optionally overlay DFG when requested)
        if options.draw_cfg:
            if cfg is None:
                raise ValueError("CFG required to draw CFG")
            G_cfg = pgv.AGraph(strict=False, directed=True)
            G_cfg.graph_attr.update(
                ranksep="0.2",
                nodesep="0.45",
                dpi=str(DEFAULT_DPI),
                rankdir="TB",
                splines=True,
                margin="0.05",
                bgcolor="white",
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
                    if (
                        getattr(options, "draw_duc", False)
                        and duc_edges is not None
                        and (node_id, succ) in duc_edges
                    ):
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

        # DFG-only graph (CFG nodes, only dashed red DFG edges)
        if getattr(options, "draw_duc", False):
            if cfg is None:
                raise ValueError("CFG required to draw DFG")
            if duc_edges is None:
                raise ValueError("Def-use information required to draw DFG")
            G_dfg = pgv.AGraph(strict=False, directed=True)
            G_dfg.graph_attr.update(
                ranksep="0.2",
                nodesep="0.45",
                dpi=str(DEFAULT_DPI),
                rankdir="TB",
                splines=True,
                margin="0.05",
                bgcolor="white",
            )
            G_dfg.node_attr.update(style="filled")
            for node_id, node in cfg.nodes.items():
                col, shape = get_node_display(node)
                G_dfg.add_node(
                    node_id, label=get_node_label(node), shape=shape, fillcolor=col
                )
            for (src, dst), names in duc_edges.items():
                dfg_label = ", ".join(sorted(names))
                G_dfg.add_edge(
                    src,
                    dst,
                    color="red",
                    style="dashed",
                    fontcolor="red",
                    label=dfg_label,
                )
            G_dfg.draw(str(self.output_path("dfg")), prog="dot")
            print(f"Saved DFG visualization: {self.output_path('dfg')}")

        # CPG: CFG with per-node AST subtree clusters and optional DFG overlay
        if options.draw_cpg:
            if cfg is None:
                raise ValueError("CFG required to draw CPG")
            G = pgv.AGraph(strict=False, directed=True)
            G.graph_attr.update(
                ranksep="0.2",
                nodesep="0.45",
                dpi=str(DEFAULT_DPI),
                rankdir="TB",
                compound="true",
                splines=True,
                margin="0.05",
                bgcolor="white",
            )
            G.node_attr.update(style="filled")

            # Add CFG nodes
            for node_id, node in cfg.nodes.items():
                label = get_node_label(node)
                color, shape = get_node_display(node)
                G.add_node(node_id, label=label, shape=shape, fillcolor=color)

            # Add CFG edges and optional DFG overlay
            for node_id, node in cfg.nodes.items():
                for successor_id in node.successors:
                    edge = (node_id, successor_id)
                    label = node.edge_labels.get(successor_id, "")
                    G.add_edge(node_id, successor_id, color="black", label=label)
                    if (
                        getattr(options, "draw_duc", False)
                        and duc_edges is not None
                        and edge in duc_edges
                    ):
                        dfg_label = ", ".join(sorted(duc_edges[edge]))
                        G.add_edge(
                            node_id,
                            successor_id,
                            color="red",
                            style="dashed",
                            fontcolor="red",
                            label=dfg_label,
                        )

            # Attach AST clusters per CFG node
            def format_ast_node_label(ts_node) -> str:
                node_type = ts_node.type if hasattr(ts_node, "type") else str(ts_node)
                text = getattr(ts_node, "text", b"") or b""
                try:
                    text_str = text.decode("utf-8")
                except Exception:
                    text_str = ""
                text_str = text_str.strip().replace("\n", " ")
                if text_str:
                    label = f"{node_type}: {text_str}"
                else:
                    label = node_type
                return truncate_ast_label(label)

            for node_id, node in cfg.nodes.items():
                ts_node = getattr(node, "ast_node", None)
                if ts_node is None:
                    continue
                cluster_name = f"cluster_ast_{node_id}"
                sg = G.add_subgraph(
                    name=cluster_name, label="", color="#DDDDDD", style="rounded,dashed"
                )
                sg.graph_attr.update(rank="TB", ranksep="0.15", nodesep="0.1")

                def add_ast_subtree(parent_ts_node):
                    parent_vis_id = f"{node_id}__ast_{parent_ts_node.id}"
                    if not G.has_node(parent_vis_id):
                        sg.add_node(
                            parent_vis_id,
                            label=format_ast_node_label(parent_ts_node),
                            shape="box",
                            fontsize=str(AST_OVERLAY_FONT_SIZE),
                            fillcolor=AST_OVERLAY_NODE_COLOR,
                            color=AST_OVERLAY_BORDER_COLOR,
                        )
                    child_nodes = [
                        c
                        for c in getattr(parent_ts_node, "children", [])
                        if (
                            not AST_OVERLAY_SHOW_ONLY_NAMED
                            or getattr(c, "is_named", False)
                        )
                    ]
                    for c in child_nodes:
                        child_vis_id = f"{node_id}__ast_{c.id}"
                        if not G.has_node(child_vis_id):
                            sg.add_node(
                                child_vis_id,
                                label=format_ast_node_label(c),
                                shape="box",
                                fontsize=str(AST_OVERLAY_FONT_SIZE),
                                fillcolor=AST_OVERLAY_NODE_COLOR,
                                color=AST_OVERLAY_BORDER_COLOR,
                            )
                        sg.add_edge(
                            parent_vis_id,
                            child_vis_id,
                            color=AST_OVERLAY_EDGE_COLOR,
                            style="solid",
                            penwidth="1",
                            arrowhead="none",
                            weight="0.2",
                            minlen="1",
                            constraint="true",
                        )
                        add_ast_subtree(c)

                root_vis_id = f"{node_id}__ast_{ts_node.id}"
                if not G.has_node(root_vis_id):
                    sg.add_node(
                        root_vis_id,
                        label=format_ast_node_label(ts_node),
                        shape="box",
                        fontsize=str(AST_OVERLAY_FONT_SIZE),
                        fillcolor=AST_OVERLAY_NODE_COLOR,
                        color=AST_OVERLAY_BORDER_COLOR,
                    )
                # Invisible constraining edge to pull cluster near CFG node
                G.add_edge(
                    node_id,
                    root_vis_id,
                    style="invis",
                    weight="5",
                    minlen="1",
                    constraint="true",
                )
                # Visible dotted connector without affecting layout
                G.add_edge(
                    node_id,
                    root_vis_id,
                    color=AST_OVERLAY_LINKING_EDGE_COLOR,
                    style="dotted",
                    penwidth="1",
                    arrowhead="none",
                    weight="0",
                    minlen="1",
                    constraint="false",
                )
                add_ast_subtree(ts_node)

            G.draw(str(self.output_path("cpg")), prog="dot")
            print(f"Saved CPG visualization: {self.output_path('cpg')}")
