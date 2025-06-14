"""
Control Flow Graph (CFG) Generator Framework using py-tree-sitter for C language.
This framework uses the visitor pattern with depth-first traversal to build CFGs.
"""

from tree_sitter_languages import get_parser
from typing import Dict, List, Set, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import graphviz


@dataclass
class CFGTraversalResult:
    """Represents the result of traversing a CFG node or subtree"""

    entry_node_id: int  # ID of the entry node of the traversed subtree
    exit_node_ids: List[int]  # IDs of the exit nodes of the traversed subtree


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


@dataclass
class CFGNode:
    """Represents a node in the Control Flow Graph"""

    id: int
    node_type: NodeType
    ast_node: Optional[Any] = None
    source_text: str = ""
    successors: Set[int] = field(default_factory=set)
    predecessors: Set[int] = field(default_factory=set)

    def add_successor(self, node_id: int):
        """Add a successor node"""
        self.successors.add(node_id)

    def add_predecessor(self, node_id: int):
        """Add a predecessor node"""
        self.predecessors.add(node_id)


class CFG:
    """Control Flow Graph representation"""

    def __init__(self, function_name: str = ""):
        self.nodes: Dict[int, CFGNode] = {}
        self.entry_node_id: Optional[int] = None
        self.exit_node_id: Optional[int] = None
        self.function_name = function_name
        self._next_id = 0

    def create_node(
        self, node_type: NodeType, ast_node: Any = None, source_text: str = ""
    ) -> int:
        """Create a new CFG node and return its ID"""
        node_id = self._next_id
        self._next_id += 1

        self.nodes[node_id] = CFGNode(
            id=node_id, node_type=node_type, ast_node=ast_node, source_text=source_text
        )

        return node_id

    def add_edge(self, from_id: int, to_id: int):
        """Add an edge between two nodes"""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].add_successor(to_id)
            self.nodes[to_id].add_predecessor(from_id)

    def set_entry(self, node_id: int):
        """Set the entry node"""
        self.entry_node_id = node_id

    def set_exit(self, node_id: int):
        """Set the exit node"""
        self.exit_node_id = node_id


class ControlFlowContext:
    """Context for tracking control flow during CFG construction"""

    def __init__(self):
        self.break_targets: List[int] = []  # Stack of break targets
        self.continue_targets: List[int] = []  # Stack of continue targets
        self.current_nodes: List[int] = []  # Current active nodes

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

    def get_break_target(self) -> Optional[int]:
        """Get the current break target"""
        return self.break_targets[-1] if self.break_targets else None

    def get_continue_target(self) -> Optional[int]:
        """Get the current continue target"""
        return self.continue_targets[-1] if self.continue_targets else None


class CFGVisitor:
    """Base visitor class for CFG construction using visitor pattern"""

    def __init__(self):
        self.cfg = CFG()
        self.context = ControlFlowContext()
        self.source_code = ""

    def visit(self, node: Any) -> CFGTraversalResult:
        """
        Visit a node and return a CFGTraversalResult containing the entry node ID and list of exit node IDs.
        This is the main entry point for the visitor pattern.
        """
        method_name = f"visit_{node.type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Any) -> CFGTraversalResult:
        """Generic visitor for unhandled node types"""
        # For leaf nodes or unhandled nodes, create a statement node
        if node.child_count == 0:
            node_id = self.cfg.create_node(
                NodeType.STATEMENT, node, self.get_source_text(node)
            )
            return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

        # For nodes with children, visit them sequentially
        entry_node = None
        current_exits = []

        for child in node.children:
            child_result = self.visit(child)

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

    def get_source_text(self, node: Any) -> str:
        """Extract source text for a node"""
        if hasattr(node, "start_byte") and hasattr(node, "end_byte"):
            return self.source_code[node.start_byte : node.end_byte]
        return str(node.type)


class CCFGVisitor(CFGVisitor):
    """C-specific CFG visitor implementation"""

    def is_linear_statement(self, node: Any) -> bool:
        """Check if a node represents a simple linear statement"""
        # Control flow statements that create branches or edges
        non_linear_types = [
            "if_statement", 
            "for_statement", 
            "while_statement", 
            "do_statement", 
            "switch_statement",
            "break_statement", 
            "continue_statement", 
            "return_statement", 
            "goto_statement",
            "compound_statement",
        ]
        
        # Check if node type isn't one of the non-linear types
        return node.type.endswith("_statement") and node.type not in non_linear_types

    def visit_expression_statement(self, node: Any) -> CFGTraversalResult:
        return self.visit_linear_statement(node)

    def visit_declaration(self, node: Any) -> CFGTraversalResult:
        return self.visit_linear_statement(node)

    def visit_linear_statement(self, node: Any) -> CFGTraversalResult:
        # If the node is a linear statement, create a statement node
        node_id = self.cfg.create_node(
            NodeType.STATEMENT, node, self.get_source_text(node)
        )
        return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

    def visit_function_definition(self, node: Any) -> CFGTraversalResult:
        """Visit a function definition"""
        # Find function name and body
        function_name = ""
        body_node = None

        for child in node.children:
            if child.type == "function_declarator":
                # Extract function name
                for subchild in child.children:
                    if subchild.type == "identifier":
                        function_name = self.get_source_text(subchild)
                        break
            elif child.type == "compound_statement":
                body_node = child

        self.cfg.function_name = function_name

        # Create entry node
        entry_id = self.cfg.create_node(
            NodeType.ENTRY, source_text=f"ENTRY: {function_name}"
        )
        self.cfg.set_entry(entry_id)

        # Create exit node
        exit_id = self.cfg.create_node(
            NodeType.EXIT, source_text=f"EXIT: {function_name}"
        )
        self.cfg.set_exit(exit_id)

        if body_node:
            # Visit function body
            body_result = self.visit(body_node)

            # Connect entry to body entry
            self.cfg.add_edge(entry_id, body_result.entry_node_id)

            # Connect body exits to function exit
            for exit_node in body_result.exit_node_ids:
                self.cfg.add_edge(exit_node, exit_id)
        else:
            # Empty function
            self.cfg.add_edge(entry_id, exit_id)

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_compound_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a compound statement (block)"""
        first_entry = None
        current_exits = []

        # Process each statement in the block
        for child in node.children:
            if child.type in ["{", "}"]:
                continue  # Skip braces

            # Visit each child
            child_result = self.visit(child)

            if first_entry is None:
                # First statement becomes the entry point for the block
                first_entry = child_result.entry_node_id
            else:
                # Connect previous statement exits to this statement's entry
                for exit_node in current_exits:
                    self.cfg.add_edge(exit_node, child_result.entry_node_id)

            # Update current exits to this statement's exits
            current_exits = child_result.exit_node_ids

        # If the block is empty, create a placeholder node
        if first_entry is None:
            placeholder_id = self.cfg.create_node(
                NodeType.STATEMENT, source_text="empty block"
            )
            first_entry = placeholder_id
            current_exits = [placeholder_id]

        return CFGTraversalResult(
            entry_node_id=first_entry, exit_node_ids=current_exits
        )

    def visit_if_statement(self, node: Any) -> CFGTraversalResult:
        """Visit an if statement"""
        condition_node = None
        then_stmt = None
        else_stmt = None

        # Parse if statement structure
        i = 0
        while i < len(node.children):
            child = node.children[i]
            if child.type == "parenthesized_expression":
                condition_node = child
            elif child.type != "if" and child.type != "else" and then_stmt is None:
                then_stmt = child
            elif child.type != "else" and then_stmt is not None:
                else_stmt = child
            i += 1

        # Create condition node
        if condition_node:
            cond_id = self.cfg.create_node(
                NodeType.CONDITION, condition_node, self.get_source_text(condition_node)
            )
        else:
            cond_id = self.cfg.create_node(
                NodeType.CONDITION, source_text="if condition"
            )

        exit_nodes = []

        # Process then branch
        if then_stmt:
            then_result = self.visit(then_stmt)
            self.cfg.add_edge(cond_id, then_result.entry_node_id)
            exit_nodes.extend(then_result.exit_node_ids)

        # Process else branch
        if else_stmt:
            else_result = self.visit(else_stmt)
            self.cfg.add_edge(cond_id, else_result.entry_node_id)
            exit_nodes.extend(else_result.exit_node_ids)
        else:
            # No else branch, condition can fall through
            exit_nodes.append(cond_id)

        return CFGTraversalResult(
            entry_node_id=cond_id, exit_node_ids=exit_nodes if exit_nodes else [cond_id]
        )

    def visit_while_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a while loop"""
        condition_node = None
        body_stmt = None

        # Parse while statement
        for child in node.children:
            if child.type == "parenthesized_expression":
                condition_node = child
            elif child.type != "while":
                body_stmt = child

        # Create loop header (condition)
        if condition_node:
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER,
                condition_node,
                f"while {self.get_source_text(condition_node)}",
            )
        else:
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER, source_text="while"
            )

        # Create exit node for the loop
        loop_exit_id = self.cfg.create_node(
            NodeType.STATEMENT, source_text="while exit"
        )

        # Set up loop context
        self.context.push_loop_context(loop_exit_id, loop_header_id)

        # Process loop body
        if body_stmt:
            body_result = self.visit(body_stmt)
            # Connect condition to body entry
            self.cfg.add_edge(loop_header_id, body_result.entry_node_id)
            # Connect body exits back to condition
            for body_exit in body_result.exit_node_ids:
                self.cfg.add_edge(body_exit, loop_header_id)

        # Connect condition to exit (false branch)
        self.cfg.add_edge(loop_header_id, loop_exit_id)

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=loop_header_id, exit_node_ids=[loop_exit_id]
        )

    def visit_for_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a for loop"""
        body_stmt = None

        # Parse for statement - this is simplified
        # In practice, you'd need more sophisticated parsing
        for child in node.children:
            if child.type == "compound_statement":
                body_stmt = child

        # Create initialization node
        init_id = self.cfg.create_node(NodeType.STATEMENT, source_text="for init")

        # Create condition node
        condition_id = self.cfg.create_node(
            NodeType.LOOP_HEADER, source_text="for condition"
        )

        # Create update node
        update_id = self.cfg.create_node(NodeType.STATEMENT, source_text="for update")

        # Create exit node
        exit_id = self.cfg.create_node(NodeType.STATEMENT, source_text="for exit")

        # Connect init to condition
        self.cfg.add_edge(init_id, condition_id)

        # Set up loop context
        self.context.push_loop_context(exit_id, update_id)

        # Process body
        if body_stmt:
            body_result = self.visit(body_stmt)
            # Connect condition to body entry
            self.cfg.add_edge(condition_id, body_result.entry_node_id)
            # Connect body exits to update
            for body_exit in body_result.exit_node_ids:
                self.cfg.add_edge(body_exit, update_id)

        # Connect update back to condition
        self.cfg.add_edge(update_id, condition_id)

        # Connect condition to exit (false branch)
        self.cfg.add_edge(condition_id, exit_id)

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=init_id, exit_node_ids=[exit_id])

    def visit_break_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a break statement"""
        break_id = self.cfg.create_node(
            NodeType.BREAK, node, self.get_source_text(node)
        )

        # Connect to break target if available
        break_target = self.context.get_break_target()
        if break_target is not None:
            self.cfg.add_edge(break_id, break_target)

        return CFGTraversalResult(
            entry_node_id=break_id, exit_node_ids=[]
        )  # Break statements don't have normal successors

    def visit_continue_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a continue statement"""
        continue_id = self.cfg.create_node(
            NodeType.CONTINUE, node, self.get_source_text(node)
        )

        # Connect to continue target if available
        continue_target = self.context.get_continue_target()
        if continue_target is not None:
            self.cfg.add_edge(continue_id, continue_target)

        return CFGTraversalResult(
            entry_node_id=continue_id, exit_node_ids=[]
        )  # Continue statements don't have normal successors

    def visit_return_statement(self, node: Any) -> CFGTraversalResult:
        """Visit a return statement"""
        return_id = self.cfg.create_node(
            NodeType.RETURN, node, self.get_source_text(node)
        )

        # Connect to function exit
        if self.cfg.exit_node_id is not None:
            self.cfg.add_edge(return_id, self.cfg.exit_node_id)

        return CFGTraversalResult(
            entry_node_id=return_id, exit_node_ids=[]
        )  # Return statements don't have normal successors


class CFGBuilder:
    """Main CFG builder class"""

    def __init__(self):
        # You'll need to install tree-sitter-c and set up the language
        # This is a placeholder - actual setup depends on your tree-sitter installation
        self.parser = None
        self.language = None

    def setup_parser(self):
        """Set up the tree-sitter parser for C"""
        self.parser = get_parser("c")
        pass

    def build_cfg(self, source_code: str) -> CFG:
        """Build CFG from C source code"""
        if not self.parser:
            raise RuntimeError("Parser not set up. Call setup_parser() first.")

        # Parse the source code
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        # Create visitor and build CFG
        visitor = CCFGVisitor()
        visitor.source_code = source_code

        # Find function definitions and process them
        for child in root_node.children:
            if child.type == "function_definition":
                visitor.visit(child)
                break  # For now, handle only the first function

        return visitor.cfg

    def visualize_cfg(self, cfg: CFG, output_file: str = "cfg"):
        """Generate a visual representation of the CFG using Graphviz"""
        dot = graphviz.Digraph(comment=f"CFG for {cfg.function_name}")
        dot.attr(rankdir="TB")

        # Add nodes
        for node_id, node in cfg.nodes.items():
            shape = "ellipse"
            color = "lightblue"

            if node.node_type == NodeType.ENTRY:
                shape = "box"
                color = "lightgreen"
            elif node.node_type == NodeType.EXIT:
                shape = "box"
                color = "lightcoral"
            elif node.node_type == NodeType.CONDITION:
                shape = "diamond"
                color = "lightyellow"
            elif node.node_type == NodeType.LOOP_HEADER:
                shape = "diamond"
                color = "lightcyan"

            label = f"{node_id}: {node.source_text[:50]}"
            dot.node(str(node_id), label, shape=shape, style="filled", fillcolor=color)

        # Add edges
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                dot.edge(str(node_id), str(successor_id))

        dot.render(output_file, format="png", cleanup=True)
        return f"{output_file}.png"


# Example usage
if __name__ == "__main__":
    # Example C code
    c_code = """
    int factorial(int n) {
        int a = 0;
        int b = 1;
        int c = 3;
        if (n <= 1) {
            return 1;
        }
        c = 10;
        int result = 1;
        for (int i = 2; i <= n; i++) {
            result *= i;
        }
        return result;
    }
    """

    print("Running example...")

    builder = CFGBuilder()
    builder.setup_parser()  # You must implement this to load tree-sitter-c

    cfg = builder.build_cfg(c_code)
    print(f"CFG built for function: {cfg.function_name}")
    print(f"Number of nodes: {len(cfg.nodes)}")
    image_path = builder.visualize_cfg(cfg)
