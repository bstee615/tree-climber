import pygraphviz as pgv
from tree_sitter import Node

from tree_sprawler.cfg.cfg_types import CFGNode
from tree_sprawler.cli.visualizers.base_visualizer import (
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


def add_dfg_edge(G: pgv.AGraph, pred: int, succ: int, dfg_label: str):
    G.add_edge(
        pred,
        succ,
        color="red",
        style="dashed",
        fontcolor="red",
        label=dfg_label,
    )


def add_cfg_node(G: pgv.AGraph, node_id: int, node: CFGNode, color: str, shape: str):
    G.add_node(node_id, label=get_node_label(node), fillcolor=color, shape=shape)


def ast_label(ts_node: Node) -> str:
    node_type = ts_node.type
    text = ts_node.text
    try:
        text_str = text.decode("utf-8").strip().replace("\n", " ")
    except Exception:
        text_str = ""
    return truncate_ast_label(f"{node_type}: {text_str}" if text_str else node_type)
