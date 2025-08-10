from collections import defaultdict
from pathlib import Path
from typing import Tuple

import pygraphviz as pgv

from tree_sprawler.ast_utils import parse_source_to_ast
from tree_sprawler.cfg.builder import CFGBuilder
from tree_sprawler.cfg.cfg_types import CFGNode, NodeType
from tree_sprawler.cli.options import AnalysisOptions
from tree_sprawler.dataflow.analyses.def_use import DefUseSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_sprawler.dataflow.solver import RoundRobinSolver

from .constants import (
    AST_OVERLAY_BORDER_COLOR,
    AST_OVERLAY_EDGE_COLOR,
    AST_OVERLAY_FONT_SIZE,
    AST_OVERLAY_LABEL_MAX,
    AST_OVERLAY_NODE_COLOR,
    AST_OVERLAY_SHOW_ONLY_NAMED,
    CONDITION_NODE_COLOR,
    CONDITION_NODE_SHAPE,
    DEFAULT_DPI,
    ENTRY_NODE_COLOR,
    ENTRY_NODE_SHAPE,
    EXIT_NODE_COLOR,
    EXIT_NODE_SHAPE,
    MAX_LABEL_LENGTH,
    REGULAR_NODE_COLOR,
    REGULAR_NODE_SHAPE,
    TRUNCATION_SUFFIX,
)


def visualize_cpg(filename: Path, options: AnalysisOptions):
    source_code = filename.read_text(encoding="utf-8")
    ast_root = parse_source_to_ast(source_code, options.language)

    builder = CFGBuilder(options.language)
    builder.setup_parser()
    cfg = builder.build_cfg(tree=ast_root)

    problem = ReachingDefinitionsProblem()
    solver = RoundRobinSolver()
    dataflow = solver.solve(cfg, problem)

    duc_solver = DefUseSolver()
    duc = duc_solver.solve(cfg, dataflow)
    duc_edges = defaultdict(set)
    for name, chains in duc.chains.items():
        for chain in chains:
            for use in chain.uses:
                duc_edges[(chain.definition, use)].add(name)

    # Build a Graphviz graph (directed) using pygraphviz
    G = pgv.AGraph(strict=False, directed=True)
    # Graph-wide attributes for layout and look
    G.graph_attr.update(
        ranksep="0.2",
        nodesep="0.45",
        dpi=str(DEFAULT_DPI),
        rankdir="TB",
        # splines="polyline",
        compound="true",
    )
    G.node_attr.update(style="filled")

    def truncate_label(text: str) -> str:
        """Truncate text labels to reasonable length."""
        if len(text) <= MAX_LABEL_LENGTH:
            return text
        return text[: MAX_LABEL_LENGTH - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX

    def truncate_ast_label(text: str) -> str:
        """Shorter truncation for AST overlay labels."""
        if len(text) <= AST_OVERLAY_LABEL_MAX:
            return text
        return (
            text[: AST_OVERLAY_LABEL_MAX - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
        )

    def get_node_label(node: CFGNode) -> str:
        """Get display label for a CFG node."""
        if node.source_text:
            return truncate_label(node.source_text.strip())
        elif node.node_type:
            return (
                node.node_type.name
                if hasattr(node.node_type, "name")
                else str(node.node_type)
            )
        return f"Node {node.id}"

    def get_node_display(node: CFGNode) -> Tuple[str, str]:
        """Get the type of a CFG node for coloring."""
        if hasattr(node, "node_type"):
            if node.node_type == NodeType.ENTRY:
                return (ENTRY_NODE_COLOR, ENTRY_NODE_SHAPE)
            elif node.node_type == NodeType.EXIT:
                return (EXIT_NODE_COLOR, EXIT_NODE_SHAPE)
            elif node.node_type in (NodeType.CONDITION, NodeType.LOOP_HEADER):
                return (CONDITION_NODE_COLOR, CONDITION_NODE_SHAPE)
        return (REGULAR_NODE_COLOR, REGULAR_NODE_SHAPE)

    # Map our marker codes to Graphviz shapes
    SHAPE_MAP = {"s": "box", "o": "ellipse", "D": "diamond"}

    # Add nodes
    for node_id, node in cfg.nodes.items():
        label = get_node_label(node)
        color, marker = get_node_display(node)
        shape = SHAPE_MAP.get(marker, "ellipse")
        G.add_node(node_id, label=label, shape=shape, fillcolor=color)

    # Add edges (CFG + DFG overlay as dashed red multi-edges)
    for node_id, node in cfg.nodes.items():
        for successor_id in node.successors:
            edge = (node_id, successor_id)
            label = node.edge_labels.get(successor_id, "")
            # Base CFG edge
            G.add_edge(node_id, successor_id, color="black", label=label)
            # DFG overlay on same endpoints, as a separate (multi) edge
            if edge in duc_edges:
                dfg_label = ", ".join(sorted(duc_edges[edge]))
                G.add_edge(
                    node_id,
                    successor_id,
                    color="red",
                    style="dashed",
                    fontcolor="red",
                    label=dfg_label,
                )

    # Attach a small AST fan-out under each CFG node to avoid clutter
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

        # Create a cluster subgraph to contain this AST tree
        cluster_name = f"cluster_ast_{node_id}"
        sg = G.add_subgraph(
            name=cluster_name, label="", color="#DDDDDD", style="rounded,dashed"
        )
        sg.graph_attr.update(rank="TB", ranksep="0.15", nodesep="0.1")

        # Recursive function to add the full AST subtree into the cluster
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
            # Optionally filter by named nodes to reduce clutter
            child_nodes = [
                c
                for c in getattr(parent_ts_node, "children", [])
                if (not AST_OVERLAY_SHOW_ONLY_NAMED or getattr(c, "is_named", False))
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

        # Ensure the root exists in the cluster, then connect CFG node → AST root
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
        # Invisible constraining edge to pull the AST cluster near the CFG node
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
            color=AST_OVERLAY_EDGE_COLOR,
            style="dotted",
            penwidth="1",
            arrowhead="none",
            weight="0",
            minlen="1",
            constraint="false",
        )
        add_ast_subtree(ts_node)
    output_path = (
        options.output_dir / f"{filename.name}_cpg.{options.output_format.value}"
    )
    prog = options.layout.value
    if options.output_format.value.lower() == "dot":
        G.write(str(output_path))
    else:
        G.draw(str(output_path), prog=prog)
    print(f"Saved CPG visualization: {output_path}")
