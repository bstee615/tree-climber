from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set

from tree_sitter import Node


class NodeType(Enum):
    """Types of CFG nodes"""

    ENTRY = auto()
    EXIT = auto()
    STATEMENT = auto()
    CONDITION = auto()
    LOOP_HEADER = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    SWITCH_HEAD = auto()
    CASE = auto()
    DEFAULT = auto()
    LABEL = auto()
    GOTO = auto()


@dataclass
class CFGNodeMetadata:
    """Metadata for a CFG node, used for debugging and analysis"""

    function_calls: List[str] = field(default_factory=list)
    variable_definitions: List[str] = field(default_factory=list)
    variable_uses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization"""
        return {
            "function_calls": self.function_calls,
            "variable_definitions": self.variable_definitions,
            "variable_uses": self.variable_uses,
        }


@dataclass
class CFGNode:
    """Represents a node in the Control Flow Graph"""

    id: int
    node_type: NodeType
    ast_node: Optional[Node] = None
    source_text: str = ""
    successors: Set[int] = field(default_factory=set)
    predecessors: Set[int] = field(default_factory=set)
    edge_labels: Dict[int, str] = field(default_factory=dict)
    metadata: CFGNodeMetadata = field(default_factory=CFGNodeMetadata)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert CFG node to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "node_type": self.node_type.name,
            "source_text": self.source_text,
            "start_index": self.ast_node.start_byte if self.ast_node else None,
            "end_index": self.ast_node.end_byte if self.ast_node else None,
            "successors": list(self.successors),
            "predecessors": list(self.predecessors),
            "edge_labels": self.edge_labels,
            "metadata": self.metadata.to_dict(),
        }


@dataclass
class CFGTraversalResult:
    """Represents the result of traversing a CFG node or subtree"""

    entry_node_id: int  # ID of the entry node of the traversed subtree
    exit_node_ids: List[int]  # IDs of the exit nodes of the traversed subtree
