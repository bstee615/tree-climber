import abc
from collections import defaultdict
from pathlib import Path
from typing import Literal, Optional, Set, Tuple

from tree_sitter import Tree

from tree_sprawler.cfg.cfg_types import CFGNode, NodeType
from tree_sprawler.cfg.visitor import CFG
from tree_sprawler.cli.options import AnalysisOptions
from tree_sprawler.dataflow.analyses.def_use import DefUseResult

from .constants import (
    AST_OVERLAY_LABEL_MAX,
    CONDITION_NODE_COLOR,
    ENTRY_NODE_COLOR,
    EXIT_NODE_COLOR,
    MAX_LABEL_LENGTH,
    REGULAR_NODE_COLOR,
    TRUNCATION_SUFFIX,
)


# Helper formatters
def truncate_label(text: str) -> str:
    return (
        text
        if len(text) <= MAX_LABEL_LENGTH
        else text[: MAX_LABEL_LENGTH - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
    )


def truncate_ast_label(text: str) -> str:
    return (
        text
        if len(text) <= AST_OVERLAY_LABEL_MAX
        else text[: AST_OVERLAY_LABEL_MAX - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX
    )


def get_node_label(node: CFGNode) -> str:
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
    if hasattr(node, "node_type"):
        if node.node_type == NodeType.ENTRY:
            return (ENTRY_NODE_COLOR, "box")
        if node.node_type == NodeType.EXIT:
            return (EXIT_NODE_COLOR, "box")
        if node.node_type in (NodeType.CONDITION, NodeType.LOOP_HEADER):
            return (CONDITION_NODE_COLOR, "diamond")
    return (REGULAR_NODE_COLOR, "ellipse")


DefUseEdges = dict[Tuple[int, int], Set[str]]


class BaseVisualizer(abc.ABC):
    def __init__(
        self,
        filename: Path,
        options: AnalysisOptions,
        ast_root: Optional[Tree],
        cfg: Optional[CFG],
        def_use: Optional[DefUseResult],
    ):
        self.filename = filename
        self.options = options
        self.ast_root = ast_root
        self.cfg = cfg
        self.def_use = def_use

    @property
    def duc_edges(self) -> Optional[DefUseEdges]:
        duc_edges = defaultdict(set)
        if self.def_use is None:
            return None
        for name, chains in self.def_use.chains.items():
            for chain in chains:
                for use in chain.uses:
                    duc_edges[(chain.definition, use)].add(name)
        return duc_edges

    @property
    def output_dir(self) -> Path:
        output_dir = self.options.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def output_path(self, name: Literal["ast", "cfg", "dfg", "cpg"]) -> Path:
        output_dir = self.output_dir
        output_ast_path = output_dir / f"{self.filename.name}_{name}.png"
        return output_ast_path

    @abc.abstractmethod
    def visualize(self):
        pass
