"""
Control Flow Graph (CFG) Generator Framework using py-tree-sitter for Go language.
This framework uses the visitor pattern with depth-first traversal to build CFGs.
Matches logic and structure of CCFGVisitor.
"""

from typing import List, Optional

from tree_sitter import Node

from tree_climber.ast_utils import (
    dfs,
    get_child_by_field_name,
    get_required_child_by_field_name,
    get_required_child_by_type,
    get_source_text,
)
from tree_climber.cfg.cfg_types import CFGTraversalResult, NodeType
from tree_climber.cfg.visitor import CFGVisitor

    
class GoCFGVisitor(CFGVisitor):
    """Go-specific CFG visitor implementation"""

    # --- Helper methods (Equivalent to CCFGVisitor helpers) ---
    def _create_condition_node(self, condition_node: Node, node_type: NodeType) -> int:
        """Create a condition/header node with proper text."""
        condition_text = get_source_text(condition_node)
        return self.create_node(node_type, condition_node, condition_text)

    def _create_body_node(
        self,
        body_node: Node,
        cfg_predecessor: int,
        cfg_successor: int,
        edge_label: Optional[str] = None,
    ) -> CFGTraversalResult:
        """Standard helper to process a body block and connect edges."""
        visit_result = self.visit(body_node)

        # Connect entry to body entry
        self.cfg.add_edge(cfg_predecessor, visit_result.entry_node_id, label=edge_label)

        # Connect body exits to function exit (or next stage)
        for exit_node in visit_result.exit_node_ids:
            self.cfg.add_edge(exit_node, cfg_successor)
        return visit_result

    def _visit_linear_statement(self, node: Node) -> CFGTraversalResult:
        """Helper for statements that just flow to the next one."""
        node_id = self.create_node(NodeType.STATEMENT, node, get_source_text(node))
        return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

    # --- AST utilities (DFG Implementation) ---
    def get_calls(self, ast_node: Node) -> List[str]:
        """Extract function calls under an AST node."""
        def process_call(node: Node) -> Optional[str]:
            if node.type == "call_expression":
                # Handle func() and obj.Method()
                fun = get_child_by_field_name(node, "function")
                if fun:
                    if fun.type == "selector_expression":
                        field = get_child_by_field_name(fun, "field")
                        return get_source_text(field) if field else None
                    return get_source_text(fun)
            return None
        return dfs(ast_node, process_call)
    
    def _is_child_of_assignment_lhs(self, node: Node) -> bool:
        """
        Helper to check if an identifier is part of the Left-Hand Side (LHS)
        of an assignment statement.
        """
        curr = node
        while curr:
            parent = curr.parent
            if not parent:
                break
            
            # Check for standard assignment: b = a + 2
            if parent.type == "assignment_statement":
                left_nodes = parent.children_by_field_name("left")
                # Need to check if 'curr' is one of the left nodes
                # or a descendant of one of the left nodes (e.g. inside expression_list)
                if curr in left_nodes:
                    return True
                # Handle expression_list wrapper (common in Go)
                for left_node in left_nodes:
                    if left_node.type == "expression_list":
                        if curr == left_node or (curr in left_node.children):
                            return True
                return False

            # Check for Short Var Declaration: a := 1
            if parent.type == "short_var_declaration":
                left_nodes = parent.children_by_field_name("left")
                if curr in left_nodes:
                    return True
                for left_node in left_nodes:
                    if left_node.type == "expression_list":
                        if curr == left_node or (curr in left_node.children):
                            return True
                return False
                
            # Stop climbing if we hit a block or function boundary to prevent false positives
            if parent.type in ("block", "function_declaration"):
                break
            
            curr = parent
        return False

    def get_definitions(self, ast_node: Node) -> List[str]:
        """Extract variable definitions (LHS of assignments/declarations)."""
        def process_definition(node: Node) -> Optional[str]:
            if node.type != "identifier":
                return None
            
            # Case 1: Variable Declarations (var a int)
            parent = node.parent
            if parent.type == "var_spec":
                if node in parent.children_by_field_name("name"):
                    return get_source_text(node)

            # Case 2: Parameters
            if parent.type == "parameter_declaration":
                # Handle (a, b int) where identifiers are siblings
                return get_source_text(node)

            # Case 3 & 4: Assignments (=) and Short Declarations (:=)
            # We use the helper to see if we are on the LHS
            if self._is_child_of_assignment_lhs(node):
                return get_source_text(node)

            return None

        return dfs(ast_node, process_definition)

    def get_uses(self, ast_node: Node) -> List[str]:
        """Extract variable uses."""
        def process_use(node: Node) -> Optional[str]:
            if node.type != "identifier":
                return None
            
            parent = node.parent
            if not parent:
                return get_source_text(node)

            # Filter out non-use contexts
            if parent.type in [
                "function_declaration", # Func name
                "method_declaration",   # Method name
                "field_declaration",    # Struct field definition
                "selector_expression",  # obj.Field (Field is not a variable use)
            ]:
                # Special case: selector. If node is the object (left), it is a use.
                if parent.type == "selector_expression":
                    operand = get_child_by_field_name(parent, "operand")
                    if node == operand:
                        return get_source_text(node)
                    return None 
                return None
            
            # In calls, the function name is typically not a variable use
            if parent.type == "call_expression":
                fun = get_child_by_field_name(parent, "function")
                if node == fun:
                    return None

            # CRITICAL FIX: Filter out LHS of assignments
            # If it IS on the LHS, it is a Definition, NOT a Use.
            if self._is_child_of_assignment_lhs(node):
                # However, check for compound assignments (+=, -=)
                # In tree-sitter-go, += is still an "assignment_statement"
                # We need to check the operator.
                p = node.parent
                while p and p.type != "assignment_statement":
                    p = p.parent
                
                if p and p.type == "assignment_statement":
                    operator = get_child_by_field_name(p, "operator")
                    if operator:
                        op_text = get_source_text(operator)
                        # If op is +=, -=, etc., it is BOTH a def and a use.
                        # If op is =, it is ONLY a def (so return None here).
                        if op_text == "=" or op_text == ":=":
                            return None
            
            return get_source_text(node)

        return dfs(ast_node, process_use)

    def is_linear_statement(self, node: Node) -> bool:
        """Check if a node represents a simple linear statement"""
        non_linear_types = [
            "if_statement",
            "for_statement",
            "expression_switch_statement",
            "type_switch_statement",
            "select_statement",
            "break_statement",
            "continue_statement",
            "return_statement",
            "goto_statement",
            "labeled_statement",
            "block",
        ]
        # Go specific: defer is technically linear in CFG construction (executes later)
        # go_statement is linear (spawns async)
        return node.is_named and node.type not in non_linear_types and node.type != "comment"

    # --- Visitor methods ---

    def visit_source_file(self, node: Node) -> CFGTraversalResult:
        """Visit the root source file node."""
        first_entry = None
        last_exits = None
        
        # In Go, top level has function declarations, method declarations, var decls, etc.
        # We focus on functions for CFG entry points.
        for child in node.children:
            if child.type in ("function_declaration", "method_declaration"):
                result = self.visit(child)
                if first_entry is None:
                    first_entry = result.entry_node_id
                last_exits = result.exit_node_ids
            # Note: Global var initializers are technically executed, but usually omitted in function-level CFGs
        
        if first_entry is None:
            # Empty file or no functions
            placeholder = self.create_node(NodeType.STATEMENT, source_text="<empty file>")
            return CFGTraversalResult(placeholder, [placeholder])

        assert last_exits is not None
        return CFGTraversalResult(entry_node_id=first_entry, exit_node_ids=last_exits)
    
    def visit_function_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a function declaration (func Main() {...})"""
        return self._visit_function_like(node)

    def visit_method_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a method declaration (func (r *Receiver) Method() {...})"""
        return self._visit_function_like(node)

    def _visit_function_like(self, node: Node) -> CFGTraversalResult:
        """Shared logic for functions and methods."""
        name_node = get_required_child_by_field_name(node, "name")
        function_name = get_source_text(name_node)
        
        # Go tree-sitter: body is a 'block' node, no field name 'body' usually
        body_node = get_required_child_by_type(node, "block")

        # Extract parameters for metadata
        parameters = []
        param_list = get_child_by_field_name(node, "parameters")
        if param_list:
             parameters = self.get_definitions(param_list)

        self.cfg.function_name = function_name

        # Create ENTRY node
        entry_id = self.create_node(NodeType.ENTRY, name_node, function_name)
        self.cfg.nodes[entry_id].metadata.variable_definitions.extend(parameters)
        self.cfg.entry_node_ids.append(entry_id)
        
        # Register context
        self.context.push_entry(entry_id)
        self.context.register_function_definition(entry_id, function_name)

        # Create EXIT node (Go function ends at the closing brace of the block)
        closing_brace = None
        if body_node and body_node.child_count > 0:
            closing_brace = body_node.children[-1] # Usually '}'
        
        exit_id = self.create_node(NodeType.EXIT, closing_brace if closing_brace else name_node, function_name)
        self.cfg.exit_node_ids.append(exit_id)
        self.context.push_exit(exit_id)

        # Process Body
        self._create_body_node(body_node, entry_id, exit_id)

        self.context.pop_entry()
        self.context.pop_exit()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_block(self, node: Node) -> CFGTraversalResult:
        """Visit a block statement { ... }."""
        first_entry = None
        current_exits = []

        # Iterate over statements inside the block
        for child in node.children:
            # Skip syntax tokens and comments
            if not child.is_named or child.type == "comment":
                continue
            
            child_result = self.visit(child)
            if not child_result: 
                continue

            if first_entry is None:
                first_entry = child_result.entry_node_id
            else:
                # Connect previous statement(s) to this one
                for exit_node in current_exits:
                    self.cfg.add_edge(exit_node, child_result.entry_node_id)
            
            current_exits = child_result.exit_node_ids

        # Empty block handling
        if first_entry is None:
            placeholder_id = self.create_node(NodeType.STATEMENT, source_text="empty block")
            first_entry = placeholder_id
            current_exits = [placeholder_id]

        return CFGTraversalResult(entry_node_id=first_entry, exit_node_ids=current_exits)

    def visit_expression_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)
    
    def visit_short_var_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)
    
    def visit_var_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_assignment_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)
    
    def visit_defer_statement(self, node: Node) -> CFGTraversalResult:
        # Treating defer as a linear statement for basic CFG
        return self._visit_linear_statement(node)
    
    def visit_go_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_if_statement(self, node: Node) -> CFGTraversalResult:
        """Visit if statement: if [init;] cond { ... } [else { ... }]"""
        initializer = get_child_by_field_name(node, "initializer")
        condition = get_required_child_by_field_name(node, "condition")
        consequence = get_required_child_by_field_name(node, "consequence") # 'consequence' is the body block
        alternative = get_child_by_field_name(node, "alternative")

        # 1. Init Phase
        entry_id = None
        init_exits = []
        if initializer:
            init_res = self.visit(initializer)
            entry_id = init_res.entry_node_id
            init_exits = init_res.exit_node_ids
        
        # 2. Condition Phase
        cond_id = self._create_condition_node(condition, NodeType.CONDITION)
        
        if entry_id is None:
            entry_id = cond_id
        else:
            for ex in init_exits:
                self.cfg.add_edge(ex, cond_id)

        # 3. Exit Phase (Merge point)
        if_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: if")

        # 4. Branches
        # True Branch
        self._create_body_node(consequence, cond_id, if_exit_id, edge_label="true")

        # False Branch
        if alternative:
            # 'alternative' can be a block (else) or another if_statement (else if)
            self._create_body_node(alternative, cond_id, if_exit_id, edge_label="false")
        else:
            self.cfg.add_edge(cond_id, if_exit_id, label="false")

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[if_exit_id])

    def visit_for_statement(self, node: Node) -> CFGTraversalResult:
        """
        Handles all Go for loops:
        1. C-style: for i:=0; i<10; i++ {}
        2. While-style: for i<10 {}
        3. Infinite: for {}
        4. Range: for i,v := range items {} (Handled by range_clause check)
        """
        initializer = get_child_by_field_name(node, "initializer") # Can be simple stmt or range_clause
        condition = get_child_by_field_name(node, "condition")
        update = get_child_by_field_name(node, "update")
        body = get_required_child_by_field_name(node, "body")

        # Check for Range Loop (Type 4)
        # In tree-sitter-go, if it's a range loop, the type of the node usually changes 
        # OR the initializer is a range_clause.
        is_range = False
        if node.type == "for_statement" and node.child_by_field_name("type") == "for_range":
             # Some parsers use different node types, but usually:
             pass 
        
        # Detect range if the first part involves 'range' keyword or node type
        # In standard tree-sitter-go:
        # `for i := range x` -> 'for_statement' where 'initializer' is 'range_clause' or 'short_var_decl' with range?
        # Actually tree-sitter-go often differentiates `for_statement` vs others. 
        # But let's assume standard structure: check if initializer is range.
        
        loop_header_id = None
        entry_id = None

        # --- Handle Initializer / Range Clause ---
        if initializer:
            if initializer.type == "range_clause":
                # Handle Range Loop Logic
                # Range acts as header + init + update implicitly
                loop_header_id = self._create_condition_node(initializer, NodeType.LOOP_HEADER)
                entry_id = loop_header_id
                
                loop_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: range loop")
                self.context.push_loop_context(loop_exit_id, loop_header_id)
                
                # Body -> Header
                self._create_body_node(body, loop_header_id, loop_header_id, edge_label="true")
                
                # Header -> Exit
                self.cfg.add_edge(loop_header_id, loop_exit_id, label="false")
                
                self.context.pop_loop_context()
                return CFGTraversalResult(entry_id, [loop_exit_id])
            else:
                # Standard Init
                init_res = self.visit(initializer)
                entry_id = init_res.entry_node_id
                init_exits = init_res.exit_node_ids

        # --- Handle Standard Loop ---
        # Create Header
        if condition:
            loop_header_id = self._create_condition_node(condition, NodeType.LOOP_HEADER)
        else:
            # Infinite or Init-only
            # If we had a range clause we wouldn't be here.
            # If no condition (for { }), header is abstract 'true'
            loop_header_id = self.create_node(NodeType.LOOP_HEADER, source_text="true (loop)")

        # Link Init -> Header
        if entry_id and entry_id != loop_header_id:
            for ex in init_exits:
                self.cfg.add_edge(ex, loop_header_id)
        else:
            entry_id = loop_header_id

        # Update Logic (continue target)
        update_entry = loop_header_id
        if update:
            # If there is an update statement, continues jump here, then back to header
            upd_res = self.visit(update)
            update_entry = upd_res.entry_node_id
            for ex in upd_res.exit_node_ids:
                self.cfg.add_edge(ex, loop_header_id)

        loop_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: for loop")

        # Context for Break/Continue
        # Continue goes to Update (if exists) or Header
        self.context.push_loop_context(loop_exit_id, update_entry)

        # Body -> Update (or Header)
        self._create_body_node(body, loop_header_id, update_entry, edge_label="true")

        # Header -> Exit (False path)
        self.cfg.add_edge(loop_header_id, loop_exit_id, label="false")

        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[loop_exit_id])

    def visit_expression_switch_statement(self, node: Node) -> CFGTraversalResult:
        """Visit switch statement."""
        initializer = get_child_by_field_name(node, "initializer")
        value = get_child_by_field_name(node, "value")
        
        # 1. Init
        entry_id = None
        init_exits = []
        if initializer:
            init_res = self.visit(initializer)
            entry_id = init_res.entry_node_id
            init_exits = init_res.exit_node_ids

        # 2. Switch Head
        if value:
            switch_head_id = self._create_condition_node(value, NodeType.SWITCH_HEAD)
        else:
            switch_head_id = self.create_node(NodeType.SWITCH_HEAD, source_text="switch true")
        
        if entry_id is None:
            entry_id = switch_head_id
        else:
            for ex in init_exits:
                self.cfg.add_edge(ex, switch_head_id)
        
        switch_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: switch")
        self.context.push_switch_context(switch_exit_id, switch_head_id)

        # 3. Cases
        # Go switch cases are children of the switch statement
        has_default = False
        for child in node.children:
            if child.type == "expression_case_clause" or child.type == "type_case_clause":
                self.visit_case_clause(child, switch_head_id, switch_exit_id)

        self.context.pop_switch_context()
        return CFGTraversalResult(entry_id, [switch_exit_id])

    def visit_type_switch_statement(self, node: Node) -> CFGTraversalResult:
        """Reuse expression switch logic for type switches (structurally similar)."""
        return self.visit_expression_switch_statement(node)

    def visit_case_clause(self, node: Node, head_id: int, exit_id: int):
        """Helper to visit individual cases."""
        # Find values/types
        case_values = []
        body_stmts = []
        
        # In Go tree-sitter: children are 'case', exprs..., ':', stmts...
        is_default = False
        for child in node.children:
            if child.type == "default":
                is_default = True
            elif child.type == "case" or child.type == ":":
                continue
            elif not child.is_named:
                continue
            elif child.type == "comment":
                continue
            
            # If it comes before the colon (heuristic) or is expression type?
            # Tree-sitter structure usually separates values. 
            # We assume anything that looks like a statement is body, else value.
            # Simplifying: if we haven't seen any statements yet, and it's an expression...
            if not self.is_linear_statement(child) and child.type not in ["block", "if_statement", "for_statement", "return_statement"]:
                 # This check is fuzzy. Better: 
                 pass 

        # Using simpler approach: standard tree-sitter-go naming
        # Unfortunately case clauses are flat. 
        # We create a Case Node.
        
        case_label = "default" if is_default else "case"
        case_node_id = self.create_node(NodeType.CASE, node, f"CASE {case_label}")
        
        # Edge from Head -> Case
        self.cfg.add_edge(head_id, case_node_id, label=case_label)

        # Process Body
        # Collect children that are statements
        stmts = []
        start_collecting = False
        for child in node.children:
            if child.type == ":":
                start_collecting = True
                continue
            if start_collecting and child.is_named:
                stmts.append(child)
        
        # Chain statements
        last_exits = [case_node_id]
        has_fallthrough = False
        
        for stmt in stmts:
            if stmt.type == "fallthrough_statement":
                has_fallthrough = True # In logic, this means connecting to next case's body
                # For basic CFG, we treat it as hitting the exit of this case block
                # Real implementation would need to link to the entry of the *next* case sibling.
                continue 

            res = self.visit(stmt)
            if res:
                for ex in last_exits:
                    self.cfg.add_edge(ex, res.entry_node_id)
                last_exits = res.exit_node_ids
        
        # Connect to Switch Exit (unless fallthrough or returns)
        # Note: Go breaks automatically.
        if not has_fallthrough:
            for ex in last_exits:
                self.cfg.add_edge(ex, exit_id)

    def visit_select_statement(self, node: Node) -> CFGTraversalResult:
        """Visit select statement (similar to switch)."""
        select_head_id = self.create_node(NodeType.SWITCH_HEAD, node, "SELECT")
        select_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: select")
        
        self.context.push_switch_context(select_exit_id, select_head_id)
        
        for child in node.children:
            if child.type == "communication_case":
                # Handle Comm Case
                self.visit_case_clause(child, select_head_id, select_exit_id)
                
        self.context.pop_switch_context()
        return CFGTraversalResult(select_head_id, [select_exit_id])

    # --- Jumps ---

    def visit_return_statement(self, node: Node) -> CFGTraversalResult:
        return_id = self.create_node(NodeType.RETURN, node, get_source_text(node))
        
        # Connect to function exit
        assert len(self.cfg.exit_node_ids) > 0, (
            "Return statement must have an exit node"
        )
        self.cfg.add_edge(return_id, self.cfg.exit_node_ids[-1])
        
        return CFGTraversalResult(entry_node_id=return_id, exit_node_ids=[])

    def visit_break_statement(self, node: Node) -> CFGTraversalResult:
        break_id = self.create_node(NodeType.BREAK, node, get_source_text(node))
        target = self.context.get_break_target() # Handles labeled breaks if context supports it
        if target:
            self.cfg.add_edge(break_id, target)
        return CFGTraversalResult(break_id, [])

    def visit_continue_statement(self, node: Node) -> CFGTraversalResult:
        cont_id = self.create_node(NodeType.CONTINUE, node, get_source_text(node))
        target = self.context.get_continue_target()
        if target:
            self.cfg.add_edge(cont_id, target)
        return CFGTraversalResult(cont_id, [])

    def visit_goto_statement(self, node: Node) -> CFGTraversalResult:
        label_node = get_child_by_field_name(node, "label")
        label_name = get_source_text(label_node) if label_node else "unknown"
        
        goto_id = self.create_node(NodeType.GOTO, node, f"goto {label_name}")
        
        # Add to context resolution
        target_id = self.context.add_goto_ref(label_name, goto_id)
        if target_id:
            self.cfg.add_edge(goto_id, target_id)
            
        return CFGTraversalResult(goto_id, [])

    def visit_labeled_statement(self, node: Node) -> CFGTraversalResult:
        label_node = get_child_by_field_name(node, "label")
        stmt = get_child_by_field_name(node, "statement") # Or just the next child
        
        label_name = get_source_text(label_node)
        label_id = self.create_node(NodeType.LABEL, label_node, label_name)
        
        # Register label
        goto_refs = self.context.add_label(label_name, label_id)
        for ref in goto_refs:
            self.cfg.add_edge(ref, label_id)
            
        # Visit body
        if stmt:
            res = self.visit(stmt)
            self.cfg.add_edge(label_id, res.entry_node_id)
            return CFGTraversalResult(label_id, res.exit_node_ids)
            
        return CFGTraversalResult(label_id, [label_id])