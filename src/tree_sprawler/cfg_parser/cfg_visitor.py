from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set


from tree_sitter import Node



class ControlFlowContext:
    """Context for tracking control flow during CFG construction"""

    def __init__(self):
        self.break_targets: List[int] = []  # Stack of break targets
        self.continue_targets: List[int] = []  # Stack of continue targets
        self.current_nodes: List[int] = []  # Current active nodes
        self.switch_head: Optional[int] = None  # Current switch statement head
        self.labels: Dict[str, int] = {}  # Map of label names to node IDs
        self.forward_goto_refs: Dict[str, List[int]] = {}  # Forward references to labels
        self.entry_node_ids: List[int] = []  # Stack of entry node IDs
        self.exit_node_ids: List[int] = []  # Stack of exit node IDs

    def push_loop_context(self, break_target: int, continue_target: int):
        """Push a new loop context"""
        self.break_targets.append(break_target)
        self.continue_targets.append(continue_target)

    def pop_loop_context(self):
        """Pop the current loop context"""
        if self.break_targets:
            self.break_targets.pop()
        if self.continue_targets:
            self.continue_targets.pop()

    def push_switch_context(self, break_target: int, switch_head: int):
        """Push a new switch context"""
        self.break_targets.append(break_target)
        self.switch_head = switch_head

    def pop_switch_context(self):
        """Pop the current switch context"""
        if self.break_targets:
            self.break_targets.pop()
        self.switch_head = None

    def push_entry(self, node_id: int):
        """Set the entry node"""
        self.entry_node_ids.append(node_id)

    def push_exit(self, node_id: int):
        """Set the exit node"""
        self.exit_node_ids.append(node_id)

    def pop_entry(self):
        """Pop the last entry node and return its ID"""
        if self.entry_node_ids:
            self.entry_node_ids.pop()

    def pop_exit(self):
        """Pop the last exit node and return its ID"""
        if self.exit_node_ids:
            self.exit_node_ids.pop()

    def get_break_target(self) -> Optional[int]:
        """Get the current break target"""
        return self.break_targets[-1] if self.break_targets else None

    def get_continue_target(self) -> Optional[int]:
        """Get the current continue target"""
        return self.continue_targets[-1] if self.continue_targets else None

    def get_switch_head(self) -> Optional[int]:
        """Get the current switch head"""
        return self.switch_head

    def add_label(self, label: str, node_id: int):
        """Register a label with its node ID"""
        self.labels[label] = node_id
        # Process any forward references to this label
        if label in self.forward_goto_refs:
            for goto_node_id in self.forward_goto_refs[label]:
                # Connect all forward references to this label
                return self.forward_goto_refs.pop(label)
        return []

    def add_goto_ref(self, label: str, goto_node_id: int):
        """Add a goto reference to a label, possibly before the label is defined"""
        if label in self.labels:
            # Label already exists, return its node ID
            return self.labels[label]
        else:
            # Label not yet defined, store as forward reference
            if label not in self.forward_goto_refs:
                self.forward_goto_refs[label] = []
            self.forward_goto_refs[label].append(goto_node_id)
            return None


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


class CFG:
    """Control Flow Graph representation"""

    def __init__(self, function_name: Optional[str] = None):
        self.nodes: Dict[int, CFGNode] = {}
        self.entry_node_ids: List[int] = []
        self.exit_node_ids: List[int] = []
        self.function_name = function_name
        self._next_id = 0

    def create_node(
        self, node_type: NodeType, ast_node: Optional[Node] = None, source_text: str = ""
    ) -> int:
        """Create a new CFG node and return its ID"""
        node_id = self._next_id
        self._next_id += 1

        self.nodes[node_id] = CFGNode(
            id=node_id, node_type=node_type, ast_node=ast_node, source_text=source_text
        )

        return node_id

    def add_edge(self, from_id: int, to_id: int, label: Optional[str] = None):
        """Add an edge between two nodes with an optional label"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].add_successor(to_id, label)
            self.nodes[to_id].add_predecessor(from_id)


@dataclass
class CFGTraversalResult:
    """Represents the result of traversing a CFG node or subtree"""

    entry_node_id: int  # ID of the entry node of the traversed subtree
    exit_node_ids: List[int]  # IDs of the exit nodes of the traversed subtree


class CFGVisitor:
    """Base visitor class for CFG construction using visitor pattern"""

    def __init__(self):
        self.cfg = CFG()
        self.context = ControlFlowContext()

    def visit(self, node: Node) -> CFGTraversalResult:
        """
        Visit a node and return a CFGTraversalResult containing the entry node ID and list of exit node IDs.
        This is the main entry point for the visitor pattern.
        """
        method_name = f"visit_{node.type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def postprocess_cfg(self):
        """
        Post-process the CFG to apply transformations after the initial construction.
        Currently implements:
        - Passthrough for ENTRY and EXIT nodes (connecting predecessors directly to successors)
        """
        self._passthrough_entry_exit_nodes()

    def _passthrough_entry_exit_nodes(self):
        """
        For ENTRY, EXIT, ELSE, CASE, and DEFAULT nodes (except the main function entry/exit):
        1. Create direct connections from predecessors to successors
        2. Remove the nodes and all their connections
        
        This applies to:
        1. Nodes with NodeType.ENTRY, NodeType.EXIT, NodeType.CASE, or NodeType.DEFAULT
        2. Nodes whose source_text starts with "ENTRY:", "EXIT:", "CASE:", or contains "else"
        """
        # Find all ENTRY, EXIT and ELSE nodes (except for the overall function entry/exit)
        special_nodes = []
        for node_id, node in self.cfg.nodes.items():
            # Skip the overall function entry/exit nodes
            if (node_id in self.cfg.entry_node_ids or node_id in self.cfg.exit_node_ids):
                continue
                
            # Check NodeType or source_text prefixes
            is_entry_exit_type = node.node_type in [NodeType.ENTRY, NodeType.EXIT]
            is_else_text = "else" in node.source_text.lower()
            is_case_node = (node.node_type == NodeType.CASE) or node.source_text.startswith("CASE:")
            is_default_node = (node.node_type == NodeType.DEFAULT) or (node.source_text == "DEFAULT")

            if any([is_entry_exit_type, is_else_text, is_case_node, is_default_node]):
                special_nodes.append(node_id)
                
        # For each special node, create direct connections between predecessors and successors
        # and then prepare to remove the node
        nodes_to_remove = []
        for node_id in special_nodes:
            node = self.cfg.nodes[node_id]
            preds = list(node.predecessors)
            succs = list(node.successors)
            
            # Connect each predecessor to each successor with proper edge labels
            for pred_id in preds:
                # Get the label for the edge coming into this node (if any)
                pred_node = self.cfg.nodes[pred_id]
                # Check if pred_node has a labeled edge to our node
                pred_to_node_label = pred_node.get_edge_label(node_id)
                
                for succ_id in succs:
                    # Get the label for the edge going out from this node (if any)
                    node_to_succ_label = node.get_edge_label(succ_id)
                    
                    # Choose which label to propagate:
                    # - If both edges have labels, prioritize the outgoing label (true/false)
                    # - Otherwise use whichever label exists
                    edge_label = node_to_succ_label if node_to_succ_label else pred_to_node_label
                    
                    # Create a direct connection with the appropriate label
                    self.cfg.add_edge(pred_id, succ_id, edge_label)
            
            # Mark node for removal
            nodes_to_remove.append(node_id)
        
        # Remove all marked nodes from the CFG
        for node_id in nodes_to_remove:
            node = self.cfg.nodes[node_id]
            
            # Remove all incoming edges
            for pred_id in list(node.predecessors):
                pred_node = self.cfg.nodes[pred_id]
                if node_id in pred_node.successors:
                    pred_node.successors.remove(node_id)
                    if node_id in pred_node.edge_labels:
                        del pred_node.edge_labels[node_id]
            
            # Remove all outgoing edges
            for succ_id in list(node.successors):
                succ_node = self.cfg.nodes[succ_id]
                if node_id in succ_node.predecessors:
                    succ_node.predecessors.remove(node_id)
            
            # Remove the node from the graph
            del self.cfg.nodes[node_id]

    def generic_visit(self, node: Node) -> CFGTraversalResult:
        """Generic visitor for unhandled node types"""
        # For leaf nodes or unhandled nodes, create a statement node
        if node.child_count == 0:
            node_id = self.cfg.create_node(
                NodeType.STATEMENT, node, get_source_text(node)
            )
            return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

        # For nodes with children, visit them sequentially
        entry_node = None
        current_exits = []

        for child in node.children:
            child_result = self.visit(child)

            # Skip if the child node returns None (like comments)
            if child_result:
                if entry_node is None:
                    # First child becomes the entry point
                    entry_node = child_result.entry_node_id
                    current_exits = child_result.exit_node_ids
                else:
                    # Connect previous exits to this child's entry
                    for prev_exit in current_exits:
                        self.cfg.add_edge(prev_exit, child_result.entry_node_id)
                    current_exits = child_result.exit_node_ids

        if entry_node is None:
            # If no children were processed, return a placeholder
            placeholder_id = self.cfg.create_node(
                NodeType.STATEMENT, source_text="empty node"
            )
            return CFGTraversalResult(
                entry_node_id=placeholder_id, exit_node_ids=[placeholder_id]
            )

        return CFGTraversalResult(entry_node_id=entry_node, exit_node_ids=current_exits)
