from typing import override

import pygraphviz as pgv

from tree_climber.cfg.cfg_types import NodeType
from tree_climber.cli.visualizers.base_visualizer import (
    BaseVisualizer,
    get_node_display,
)
from tree_climber.cli.visualizers.utils import add_cfg_node, add_dfg_edge

from .constants import DEFAULT_DPI


class DFGVisualizer(BaseVisualizer):
    @override
    def visualize(self):
        options = self.options
        cfg = self.cfg
        duc_edges = self.duc_edges
        if not options.draw_dfg:
            return

        if cfg is None:
            raise ValueError("CFG required to draw DFG")
        if duc_edges is None:
            raise ValueError("Def-use information required to draw DFG")

        # DFG-only graph (CFG nodes, only dashed red DFG edges)
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
            if node.node_type in (NodeType.ENTRY, NodeType.EXIT):
                continue
            col, shape = get_node_display(node)
            add_cfg_node(G_dfg, node_id, node, color=col, shape=shape)
        for (src, dst), names in duc_edges.items():
            dfg_label = ", ".join(sorted(names))
            add_dfg_edge(G_dfg, src, dst, dfg_label)
        G_dfg.draw(str(self.output_path("dfg")), prog="dot")
        print(f"Saved DFG visualization: {self.output_path('dfg')}")
