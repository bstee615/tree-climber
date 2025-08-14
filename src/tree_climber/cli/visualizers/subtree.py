from typing import override

import pygraphviz as pgv

from tree_climber.cli.visualizers.base_visualizer import (
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
        cfg = self.cfg
        duc_edges = self.duc_edges

        # CPG: CFG with per-node AST subtree clusters and optional DFG overlay
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
                        not AST_OVERLAY_SHOW_ONLY_NAMED or getattr(c, "is_named", False)
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
