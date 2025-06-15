from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from tree_sitter import Node


class NodeType(Enum):
    """Types of CFG nodes"""

    ENTRY = "entry"
    EXIT = "exit"
    STATEMENT = "statement"
    CONDITION = "condition"
    LOOP_HEADER = "loop_header"
    BREAK = "break"
    CONTINUE = "continue"
    RETURN = "return"
    SWITCH_HEAD = "switch_head"
    CASE = "case"
    DEFAULT = "default"
    LABEL = "label"
    GOTO = "goto"


@dataclass
class CFGNode:
    """Represents a node in the Control Flow Graph"""

    id: int
    node_type: NodeType
    ast_node: Optional[Node] = None
    source_text: str = ""
    successors: Set[int] = field(default_factory=set)
    predecessors: Set[int] = field(default_factory=set)
    # Dictionary to store edge labels: {successor_id: label}
    edge_labels: Dict[int, str] = field(default_factory=dict)

    def add_successor(self, node_id: int, label: Optional[str] = None):
        """Add a successor node with an optional label"""
        self.successors.add(node_id)
        if label is not None:
            self.edge_labels[node_id] = label

    def add_predecessor(self, node_id: int):
        """Add a predecessor node"""
        self.predecessors.add(node_id)

    def get_edge_label(self, successor_id: int) -> Optional[str]:
        """Get the label for an edge to a successor, if it exists"""
        return self.edge_labels.get(successor_id)


@dataclass
class CFGTraversalResult:
    """Represents the result of traversing a CFG node or subtree"""

    entry_node_id: int  # ID of the entry node of the traversed subtree
    exit_node_ids: List[int]  # IDs of the exit nodes of the traversed subtree
