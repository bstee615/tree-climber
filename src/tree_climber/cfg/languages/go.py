"""
Control Flow Graph (CFG) Generator Framework using py-tree-sitter for Go language.
This framework uses the visitor pattern with depth-first traversal to build CFGs.
"""

from typing import List, Optional

from tree_sitter import Node

from tree_climber.ast_utils import (
    dfs,
    get_child_by_field_name,
    get_required_child_by_field_name,
    get_source_text,
)
from tree_climber.cfg.cfg_types import CFGTraversalResult, NodeType
from tree_climber.cfg.visitor import CFGVisitor


class GoCFGVisitor(CFGVisitor):
    """Go-specific CFG visitor implementation"""

    # Helper methods
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
        visit_result = self.visit(body_node)

        # Connect entry to body entry
        self.cfg.add_edge(cfg_predecessor, visit_result.entry_node_id, label=edge_label)

        # Connect body exits to function exit
        for exit_node in visit_result.exit_node_ids:
            self.cfg.add_edge(exit_node, cfg_successor)
        return visit_result

    def _visit_linear_statement(self, node: Node) -> CFGTraversalResult:
        # If the node is a linear statement, create a statement node
        node_id = self.create_node(NodeType.STATEMENT, node, get_source_text(node))
        return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

    # AST utilities
    def get_calls(self, ast_node: Node) -> List[str]:
        """Extract function calls under an AST node."""

        def process_call(node: Node) -> Optional[str]:
            if node.type == "call_expression":
                # Get the function identifier
                function = get_child_by_field_name(node, "function")
                if function:
                    if function.type == "identifier":
                        return get_source_text(function)
                    elif function.type == "selector_expression":
                        # Handle method calls like obj.Method()
                        field = get_child_by_field_name(function, "field")
                        if field:
                            return get_source_text(field)
                return None
            return None

        return dfs(ast_node, process_call)

    def get_definitions(self, ast_node: Node) -> List[str]:
        """Extract variable definitions under an AST node."""

        def process_definition(node: Node) -> Optional[str]:
            # Short variable declaration: x := 10
            if node.type == "short_var_declaration":
                left = get_child_by_field_name(node, "left")
                if left:
                    for child in left.children:
                        if child.type == "identifier":
                            return get_source_text(child)
            # Variable declaration: var x int
            elif node.type == "var_spec":
                for child in node.children:
                    if child.type == "identifier":
                        return get_source_text(child)
            # Assignment expression
            elif node.type == "assignment_expression":
                left = get_child_by_field_name(node, "left")
                if left:
                    if left.type == "identifier":
                        return get_source_text(left)
                    # Handle multiple assignments
                    elif left.type == "expression_list":
                        for child in left.children:
                            if child.type == "identifier":
                                return get_source_text(child)
            # Increment/decrement
            elif node.type in ("inc_statement", "dec_statement"):
                for child in node.children:
                    if child.type == "identifier":
                        return get_source_text(child)
            # Range clause in for loops
            elif node.type == "range_clause":
                left = get_child_by_field_name(node, "left")
                if left:
                    if left.type == "identifier":
                        return get_source_text(left)
                    elif left.type == "expression_list":
                        for child in left.children:
                            if child.type == "identifier":
                                return get_source_text(child)
            return None

        return dfs(ast_node, process_definition)

    def get_uses(self, ast_node: Node) -> List[str]:
        """Extract variable uses under an AST node."""

        def process_use(node: Node) -> Optional[str]:
            if node.type == "identifier":
                # Skip identifiers in various contexts where they're not "uses"
                if node.parent:
                    if node.parent.type in [
                        "call_expression",  # Function names in calls
                        "function_declaration",  # Function names in definitions
                        "parameter_declaration",  # Parameter declarations
                        "var_spec",  # Variable declarations
                        "short_var_declaration",  # Short var declarations
                        "field_declaration",  # Struct field declarations
                        "type_spec",  # Type declarations
                    ]:
                        return None
                    # Skip identifiers on the left side of assignments
                    if node.parent.type == "assignment_expression":
                        left = get_child_by_field_name(node.parent, "left")
                        if left and (left == node or node in left.children):
                            # Check if it's a compound assignment
                            operator = get_child_by_field_name(node.parent, "operator")
                            if operator and get_source_text(operator) in (
                                "+=",
                                "-=",
                                "*=",
                                "/=",
                                "%=",
                                "&=",
                                "|=",
                                "^=",
                                "<<=",
                                ">>=",
                                "&^=",
                            ):
                                return get_source_text(node)
                            return None
                    # Increment/decrement are both uses and definitions
                    if node.parent.type in ("inc_statement", "dec_statement"):
                        return get_source_text(node)
                return get_source_text(node)
            return None

        return dfs(ast_node, process_use)

    def is_linear_statement(self, node: Node) -> bool:
        """Check if a node represents a simple linear statement"""
        # Control flow statements that create branches or edges
        non_linear_types = [
            "if_statement",
            "for_statement",
            "switch_statement",
            "type_switch_statement",
            "select_statement",
            "break_statement",
            "continue_statement",
            "return_statement",
            "goto_statement",
            "block",
        ]

        # Check if node type isn't one of the non-linear types
        return node.type.endswith("_statement") and node.type not in non_linear_types

    # Visitor methods
    def visit_comment(self, node: Node) -> None:
        """Skip comment nodes entirely"""
        return None

    def visit_expression_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_short_var_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_var_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_const_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_assignment_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_inc_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_dec_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_send_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_go_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a go statement (goroutine launch)"""
        return self._visit_linear_statement(node)

    def visit_defer_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a defer statement"""
        return self._visit_linear_statement(node)

    def _find_func_literal(self, node: Node) -> Optional[Node]:
        """Find a func_literal node within a var_declaration"""
        for child in node.children:
            if child.type == "var_spec":
                for spec_child in child.children:
                    if spec_child.type == "func_literal":
                        return spec_child
                    # Check in expression_list
                    elif spec_child.type == "expression_list":
                        for expr in spec_child.children:
                            if expr.type == "func_literal":
                                return expr
        return None

    def _extract_var_name(self, node: Node) -> str:
        """Extract variable name from a var_declaration"""
        for child in node.children:
            if child.type == "var_spec":
                for spec_child in child.children:
                    if spec_child.type == "identifier":
                        return get_source_text(spec_child)
        return "anonymous"

    def visit_func_literal(self, node: Node, func_name: str = "anonymous") -> CFGTraversalResult:
        """Visit a function literal (anonymous function)"""
        # Get components via named fields
        parameters = get_child_by_field_name(node, "parameters")
        body_node = get_child_by_field_name(node, "body")

        # Extract parameters
        param_list = []
        if parameters:
            for child in parameters.children:
                if child.type == "parameter_declaration":
                    for param_child in child.children:
                        if param_child.type == "identifier":
                            param_list.append(get_source_text(param_child))

        # If there's no body, create a simple entry/exit
        if body_node is None:
            entry_id = self.create_node(
                NodeType.ENTRY, source_text=func_name, ast_node=node
            )
            exit_id = self.create_node(
                NodeType.EXIT, source_text=func_name, ast_node=node
            )
            self.cfg.add_edge(entry_id, exit_id)
            return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

        # Find closing brace in body for exit node location
        closing_brace = None
        for child in body_node.children:
            if child.type == "}":
                closing_brace = child

        self.cfg.function_name = func_name

        # Create entry node with function name and parameters
        entry_id = self.create_node(
            NodeType.ENTRY, source_text=func_name, ast_node=node
        )
        self.cfg.nodes[entry_id].metadata.variable_definitions.extend(param_list)
        self.cfg.entry_node_ids.append(entry_id)
        self.context.push_entry(entry_id)
        self.context.register_function_definition(entry_id, func_name)

        # Create exit node
        exit_id = self.create_node(
            NodeType.EXIT, source_text=func_name, ast_node=closing_brace
        )
        self.cfg.exit_node_ids.append(exit_id)
        self.context.push_exit(exit_id)

        self._create_body_node(body_node, entry_id, exit_id)

        self.context.pop_entry()
        self.context.pop_exit()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_source_file(self, node: Node) -> CFGTraversalResult:
        """Visit the root source file node"""
        first_entry = None
        last_exits = None
        for child in node.children:
            result = None
            if child.type in ("function_declaration", "method_declaration"):
                result = self.visit(child)
            elif child.type == "var_declaration":
                # Check if this is a function literal assigned to a variable
                func_literal = self._find_func_literal(child)
                if func_literal:
                    # Extract variable name for the function
                    var_name = self._extract_var_name(child)
                    result = self.visit_func_literal(func_literal, var_name)
            
            if result:
                if first_entry is None:
                    first_entry = result.entry_node_id
                last_exits = result.exit_node_ids

        assert first_entry is not None, (
            "Source file must have at least one entry node"
        )
        assert last_exits is not None, "Source file must have at least one exit node"
        return CFGTraversalResult(
            entry_node_id=first_entry,
            exit_node_ids=last_exits,
        )

    def visit_function_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a function declaration"""
        # Get components via named fields
        name_node = get_required_child_by_field_name(node, "name")
        parameters = get_child_by_field_name(node, "parameters")
        body_node = get_child_by_field_name(node, "body")

        # Extract function name
        function_name = get_source_text(name_node)

        # Extract parameters
        param_list = []
        if parameters:
            for child in parameters.children:
                if child.type == "parameter_declaration":
                    # Get parameter names
                    for param_child in child.children:
                        if param_child.type == "identifier":
                            param_list.append(get_source_text(param_child))

        # If there's no body (function signature only), create a simple entry/exit
        if body_node is None:
            entry_id = self.create_node(
                NodeType.ENTRY, source_text=function_name, ast_node=name_node
            )
            exit_id = self.create_node(
                NodeType.EXIT, source_text=function_name, ast_node=name_node
            )
            self.cfg.add_edge(entry_id, exit_id)
            return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

        # Find closing brace in body for exit node location
        closing_brace = None
        for child in body_node.children:
            if child.type == "}":
                closing_brace = child

        self.cfg.function_name = function_name

        # Create entry node with function name and parameters
        entry_id = self.create_node(
            NodeType.ENTRY, source_text=function_name, ast_node=name_node
        )
        self.cfg.nodes[entry_id].metadata.variable_definitions.extend(param_list)
        self.cfg.entry_node_ids.append(entry_id)
        self.context.push_entry(entry_id)
        self.context.register_function_definition(entry_id, function_name)

        # Create exit node
        exit_id = self.create_node(
            NodeType.EXIT, source_text=function_name, ast_node=closing_brace
        )
        self.cfg.exit_node_ids.append(exit_id)
        self.context.push_exit(exit_id)

        self._create_body_node(body_node, entry_id, exit_id)

        self.context.pop_entry()
        self.context.pop_exit()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_method_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a method declaration"""
        # Get components via named fields
        name_node = get_required_child_by_field_name(node, "name")
        receiver = get_child_by_field_name(node, "receiver")
        parameters = get_child_by_field_name(node, "parameters")
        body_node = get_child_by_field_name(node, "body")

        # Extract method name
        method_name = get_source_text(name_node)

        # Extract receiver
        param_list = []
        if receiver:
            for child in receiver.children:
                if child.type == "parameter_declaration":
                    for param_child in child.children:
                        if param_child.type == "identifier":
                            param_list.append(get_source_text(param_child))

        # Extract parameters
        if parameters:
            for child in parameters.children:
                if child.type == "parameter_declaration":
                    for param_child in child.children:
                        if param_child.type == "identifier":
                            param_list.append(get_source_text(param_child))

        # If there's no body, create a simple entry/exit
        if body_node is None:
            entry_id = self.create_node(
                NodeType.ENTRY, source_text=method_name, ast_node=name_node
            )
            exit_id = self.create_node(
                NodeType.EXIT, source_text=method_name, ast_node=name_node
            )
            self.cfg.add_edge(entry_id, exit_id)
            return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

        # Find closing brace in body for exit node location
        closing_brace = None
        for child in body_node.children:
            if child.type == "}":
                closing_brace = child

        self.cfg.function_name = method_name

        # Create entry node with method name and parameters
        entry_id = self.create_node(
            NodeType.ENTRY, source_text=method_name, ast_node=name_node
        )
        self.cfg.nodes[entry_id].metadata.variable_definitions.extend(param_list)
        self.cfg.entry_node_ids.append(entry_id)
        self.context.push_entry(entry_id)
        self.context.register_function_definition(entry_id, method_name)

        # Create exit node
        exit_id = self.create_node(
            NodeType.EXIT, source_text=method_name, ast_node=closing_brace
        )
        self.cfg.exit_node_ids.append(exit_id)
        self.context.push_exit(exit_id)

        self._create_body_node(body_node, entry_id, exit_id)

        self.context.pop_entry()
        self.context.pop_exit()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_block(self, node: Node) -> CFGTraversalResult:
        """Visit a block (compound statement)"""
        first_entry = None
        current_exits = []

        # Process each statement in the block
        for child in node.children:
            # Skip unnamed nodes and comments
            if not child.is_named or child.type == "comment":
                continue

            child_result = self.visit(child)
            if child_result is None:  # Skip nodes that return None
                continue

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
            placeholder_id = self.create_node(
                NodeType.STATEMENT, source_text="empty block"
            )
            first_entry = placeholder_id
            current_exits = [placeholder_id]

        return CFGTraversalResult(
            entry_node_id=first_entry, exit_node_ids=current_exits
        )

    def visit_if_statement(self, node: Node) -> CFGTraversalResult:
        """Visit an if statement"""
        # Get components via named fields
        initializer = get_child_by_field_name(node, "initializer")
        condition_node = get_required_child_by_field_name(node, "condition")
        consequence = get_required_child_by_field_name(node, "consequence")
        alternative = get_child_by_field_name(node, "alternative")

        # Handle initializer if present (e.g., if x := foo(); x > 0)
        entry_id = None
        if initializer:
            init_result = self.visit(initializer)
            entry_id = init_result.entry_node_id
            # Create condition node
            cond_id = self._create_condition_node(condition_node, NodeType.CONDITION)
            # Connect initializer to condition
            for exit_node in init_result.exit_node_ids:
                self.cfg.add_edge(exit_node, cond_id)
        else:
            # Create condition node
            cond_id = self._create_condition_node(condition_node, NodeType.CONDITION)
            entry_id = cond_id

        # Create an explicit exit node for the if statement
        if_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: if stmt")

        # Process then branch with "true" label
        self._create_body_node(consequence, cond_id, if_exit_id, edge_label="true")

        # Process else branch with "false" label
        if alternative:
            self._create_body_node(alternative, cond_id, if_exit_id, edge_label="false")
        else:
            # No else branch, direct false path to the exit node
            self.cfg.add_edge(cond_id, if_exit_id, "false")

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[if_exit_id])

    def visit_for_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a for loop (handles all Go for loop variants)"""
        # Get components via named fields
        initializer = get_child_by_field_name(node, "initializer")
        condition = get_child_by_field_name(node, "condition")
        update = get_child_by_field_name(node, "update")
        body = get_required_child_by_field_name(node, "body")

        # Handle different for loop types
        # 1. Infinite loop: for { }
        # 2. Condition only: for x > 0 { }
        # 3. Classic three-part: for i := 0; i < 10; i++ { }
        # 4. Range loop: for k, v := range slice { }

        entry_id = None
        condition_id = None
        update_id = None

        # Create initialization node if present
        if initializer:
            if initializer.type == "range_clause":
                # Range loop
                return self._visit_range_for(initializer, body)
            else:
                init_result = self.visit(initializer)
                entry_id = init_result.entry_node_id

        # Create condition node
        if condition:
            condition_text = get_source_text(condition)
            condition_id = self.create_node(
                NodeType.LOOP_HEADER, condition, condition_text
            )
        else:
            # Infinite loop or range loop without condition
            condition_id = self.create_node(NodeType.LOOP_HEADER, source_text="true")

        # If no initializer, condition is the entry
        if entry_id is None:
            entry_id = condition_id
        else:
            # Connect initializer to condition
            self.cfg.add_edge(entry_id, condition_id)

        # Create update node if present
        if update:
            update_result = self.visit(update)
            update_id = update_result.entry_node_id
        else:
            # No update, use condition as continue target
            update_id = condition_id

        # Create exit node
        exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: for loop")

        # Set up loop context
        self.context.push_loop_context(exit_id, update_id)

        # Process body
        self._create_body_node(body, condition_id, update_id, edge_label="true")

        # Connect update back to condition if it exists
        if update_id != condition_id:
            self.cfg.add_edge(update_id, condition_id)

        # Connect condition to exit (false branch)
        self.cfg.add_edge(condition_id, exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def _visit_range_for(
        self, range_clause: Node, body: Node
    ) -> CFGTraversalResult:
        """Visit a for-range loop"""
        # Extract range expression
        right = get_child_by_field_name(range_clause, "right")
        range_text = f"range {get_source_text(right)}" if right else "range"

        # Create loop header
        loop_header_id = self.create_node(
            NodeType.LOOP_HEADER, range_clause, range_text
        )

        # Create exit node
        exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: for-range loop")

        # Set up loop context
        self.context.push_loop_context(exit_id, loop_header_id)

        # Process body
        self._create_body_node(body, loop_header_id, loop_header_id, edge_label="true")

        # Connect condition to exit
        self.cfg.add_edge(loop_header_id, exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=loop_header_id, exit_node_ids=[exit_id]
        )

    def visit_break_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a break statement"""
        break_id = self.create_node(NodeType.BREAK, node, get_source_text(node))

        # Connect to break target if available
        break_target = self.context.get_break_target()
        assert break_target is not None, "Break statement must have a target"
        self.cfg.add_edge(break_id, break_target)

        return CFGTraversalResult(entry_node_id=break_id, exit_node_ids=[])

    def visit_continue_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a continue statement"""
        continue_id = self.create_node(NodeType.CONTINUE, node, get_source_text(node))

        # Connect to continue target if available
        continue_target = self.context.get_continue_target()
        assert continue_target is not None, "Continue statement must have a target"
        self.cfg.add_edge(continue_id, continue_target)

        return CFGTraversalResult(entry_node_id=continue_id, exit_node_ids=[])

    def visit_return_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a return statement"""
        return_id = self.create_node(NodeType.RETURN, node, get_source_text(node))

        # Connect to function exit
        assert len(self.cfg.exit_node_ids) > 0, (
            "Return statement must have an exit node"
        )
        self.cfg.add_edge(return_id, self.cfg.exit_node_ids[-1])

        return CFGTraversalResult(entry_node_id=return_id, exit_node_ids=[])

    def visit_switch_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a switch statement"""
        # Get components via named fields
        initializer = get_child_by_field_name(node, "initializer")
        value = get_child_by_field_name(node, "value")
        body = get_required_child_by_field_name(node, "body")

        entry_id = None

        # Handle initializer if present
        if initializer:
            init_result = self.visit(initializer)
            entry_id = init_result.entry_node_id

        # Create switch head node
        if value:
            switch_head_id = self._create_condition_node(value, NodeType.SWITCH_HEAD)
        else:
            # Switch without expression (like switch { case x: ... })
            switch_head_id = self.create_node(NodeType.SWITCH_HEAD, source_text="true")

        # Connect initializer to switch head if present
        if entry_id is not None:
            for exit_node in [entry_id]:
                self.cfg.add_edge(exit_node, switch_head_id)
        else:
            entry_id = switch_head_id

        # Create exit node for the switch
        switch_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: switch")

        # Set up switch context for break statements
        self.context.push_switch_context(switch_exit_id, switch_head_id)

        # Process switch body
        self._create_body_node(body, switch_head_id, switch_exit_id)

        # Clean up switch context
        self.context.pop_switch_context()

        return CFGTraversalResult(
            entry_node_id=entry_id, exit_node_ids=[switch_exit_id]
        )

    def visit_expression_switch_statement(
        self, node: Node
    ) -> CFGTraversalResult:
        """Visit an expression switch statement (alias for switch_statement)"""
        return self.visit_switch_statement(node)

    def visit_type_switch_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a type switch statement"""
        # Similar to regular switch but for type assertions
        initializer = get_child_by_field_name(node, "initializer")
        alias = get_child_by_field_name(node, "alias")
        value = get_child_by_field_name(node, "value")
        body = get_required_child_by_field_name(node, "body")

        entry_id = None

        # Handle initializer if present
        if initializer:
            init_result = self.visit(initializer)
            entry_id = init_result.entry_node_id

        # Create switch head node with type assertion
        switch_text = f"{get_source_text(alias)} := {get_source_text(value)}" if alias and value else "type switch"
        switch_head_id = self.create_node(
            NodeType.SWITCH_HEAD, source_text=switch_text
        )

        # Connect initializer to switch head if present
        if entry_id is not None:
            self.cfg.add_edge(entry_id, switch_head_id)
        else:
            entry_id = switch_head_id

        # Create exit node
        switch_exit_id = self.create_node(
            NodeType.EXIT, source_text="EXIT: type switch"
        )

        # Set up switch context
        self.context.push_switch_context(switch_exit_id, switch_head_id)

        # Process switch body
        self._create_body_node(body, switch_head_id, switch_exit_id)

        # Clean up switch context
        self.context.pop_switch_context()

        return CFGTraversalResult(
            entry_node_id=entry_id, exit_node_ids=[switch_exit_id]
        )

    def visit_expression_case_clause(self, node: Node) -> CFGTraversalResult:
        """Visit a case clause in a switch statement"""
        # Get case value(s)
        value_nodes = []
        statements = []

        for child in node.children:
            if child.type == "case":
                continue
            elif child.type == "default":
                continue
            elif child.type == ":":
                continue
            elif child.type == "expression_list":
                # Multiple case values
                for expr in child.children:
                    if expr.is_named:
                        value_nodes.append(expr)
            elif child.is_named and not statements:
                # First named child that's not a statement is likely the value
                value_nodes.append(child)
            else:
                # Remaining named children are statements
                if child.is_named:
                    statements.append(child)

        # Create case node
        if value_nodes:
            value_text = ", ".join(get_source_text(v) for v in value_nodes)
            case_id = self.create_node(
                NodeType.CASE, value_nodes[0], f"CASE: {value_text}"
            )
        else:
            # Default case
            case_id = self.create_node(NodeType.CASE, source_text="DEFAULT")
            value_text = "default"

        # Connect case to switch head if available
        switch_head = self.context.get_switch_head()
        if switch_head is not None:
            self.cfg.add_edge(switch_head, case_id, value_text)

        exit_nodes = [case_id]  # Default exit for fall-through

        # Process statements in the case body
        if statements:
            last_exits = [case_id]

            for stmt in statements:
                if not stmt.is_named or stmt.type == "comment":
                    continue

                stmt_result = self.visit(stmt)
                if stmt_result:
                    # Connect last exits to this statement's entry
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    last_exits = stmt_result.exit_node_ids

                    # If no exits, no fall-through
                    if not last_exits:
                        exit_nodes = []
                        break

            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=case_id, exit_node_ids=exit_nodes)

    def visit_type_case_clause(self, node: Node) -> CFGTraversalResult:
        """Visit a case clause in a type switch statement"""
        # Similar to expression_case_clause but for types
        type_nodes = []
        statements = []

        for child in node.children:
            if child.type in ("case", "default", ":"):
                continue
            elif child.type == "type_list":
                for type_node in child.children:
                    if type_node.is_named:
                        type_nodes.append(type_node)
            elif child.is_named and not statements:
                type_nodes.append(child)
            else:
                if child.is_named:
                    statements.append(child)

        # Create case node
        if type_nodes:
            type_text = ", ".join(get_source_text(t) for t in type_nodes)
            case_id = self.create_node(
                NodeType.CASE, type_nodes[0], f"TYPE: {type_text}"
            )
        else:
            case_id = self.create_node(NodeType.CASE, source_text="DEFAULT")
            type_text = "default"

        # Connect case to switch head
        switch_head = self.context.get_switch_head()
        if switch_head is not None:
            self.cfg.add_edge(switch_head, case_id, type_text)

        exit_nodes = [case_id]

        # Process statements
        if statements:
            last_exits = [case_id]

            for stmt in statements:
                if not stmt.is_named or stmt.type == "comment":
                    continue

                stmt_result = self.visit(stmt)
                if stmt_result:
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    last_exits = stmt_result.exit_node_ids

                    if not last_exits:
                        exit_nodes = []
                        break

            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=case_id, exit_node_ids=exit_nodes)

    def visit_select_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a select statement (for channel operations)"""
        body = get_required_child_by_field_name(node, "body")

        # Create select head node
        select_head_id = self.create_node(
            NodeType.SWITCH_HEAD, node, "SELECT"
        )  # Reuse SWITCH_HEAD type

        # Create exit node
        select_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: select")

        # Set up select context (similar to switch)
        self.context.push_switch_context(select_exit_id, select_head_id)

        # Process select body
        self._create_body_node(body, select_head_id, select_exit_id)

        # Clean up context
        self.context.pop_switch_context()

        return CFGTraversalResult(
            entry_node_id=select_head_id, exit_node_ids=[select_exit_id]
        )

    def visit_communication_case(self, node: Node) -> CFGTraversalResult:
        """Visit a case clause in a select statement"""
        # Get communication operation
        comm = get_child_by_field_name(node, "communication")
        statements = []

        for child in node.children:
            if child == comm or child.type in ("case", "default", ":"):
                continue
            if child.is_named:
                statements.append(child)

        # Create case node
        if comm:
            comm_text = get_source_text(comm)
            case_id = self.create_node(NodeType.CASE, comm, f"CASE: {comm_text}")
            value_text = comm_text
        else:
            case_id = self.create_node(NodeType.CASE, source_text="DEFAULT")
            value_text = "default"

        # Connect case to select head
        select_head = self.context.get_switch_head()
        if select_head is not None:
            self.cfg.add_edge(select_head, case_id, value_text)

        exit_nodes = [case_id]

        # Process statements
        if statements:
            last_exits = [case_id]

            for stmt in statements:
                if not stmt.is_named or stmt.type == "comment":
                    continue

                stmt_result = self.visit(stmt)
                if stmt_result:
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    last_exits = stmt_result.exit_node_ids

                    if not last_exits:
                        exit_nodes = []
                        break

            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=case_id, exit_node_ids=exit_nodes)

    def visit_labeled_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a labeled statement - target for goto statements"""
        # Get components via named fields
        label_node = get_required_child_by_field_name(node, "label")
        label_name = get_source_text(label_node)

        # Get the statement after label
        body_stmt = None
        for child in node.children:
            if child != label_node and child.type != ":":
                body_stmt = child
                break

        # Create label node
        label_id = self.create_node(NodeType.LABEL, label_node, label_name)

        # Register label in context
        goto_refs = self.context.add_label(label_name, label_id)
        # Connect any forward goto references to this label
        for goto_id in goto_refs:
            self.cfg.add_edge(goto_id, label_id)

        # Process body statement
        if body_stmt:
            body_result = self.visit(body_stmt)
            self.cfg.add_edge(label_id, body_result.entry_node_id)
            return CFGTraversalResult(
                entry_node_id=label_id, exit_node_ids=body_result.exit_node_ids
            )

        return CFGTraversalResult(entry_node_id=label_id, exit_node_ids=[label_id])

    def visit_goto_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a goto statement - unconditional jump to a label"""
        # Get label via named field
        label_node = get_required_child_by_field_name(node, "label")
        target_label = get_source_text(label_node)

        # Create goto node
        goto_id = self.create_node(NodeType.GOTO, node, f"goto {target_label}")

        # Try to connect to label if it exists
        target_id = self.context.add_goto_ref(target_label, goto_id)
        if target_id:
            # If label already defined, connect goto to label
            self.cfg.add_edge(goto_id, target_id)

        # Goto statements don't have normal successors
        return CFGTraversalResult(entry_node_id=goto_id, exit_node_ids=[])

    def visit_fallthrough_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a fallthrough statement in a switch"""
        fallthrough_id = self.create_node(
            NodeType.STATEMENT, node, get_source_text(node)
        )
        # Fallthrough is handled by the case clause visitor through exit_node_ids
        # Return with exit nodes to indicate fall-through continues
        return CFGTraversalResult(
            entry_node_id=fallthrough_id, exit_node_ids=[fallthrough_id]
        )


def main():
    """Main function to test Go CFG generation"""
    import os
    import sys

    from tree_sitter_languages import get_parser

    from tree_climber.cfg.visualization import visualize_cfg

    # Read the test file
    try:
        # test_file = os.path.join(
        #     os.path.dirname(
        #         os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        #     ),
        #     "tree_climber",
        #     "test",
        #     "test.go",
        # )
        test_file = "/home/nguyenducduong/hienlt/treeclimber/test/test.go"
        with open(test_file, "r") as f:
            source_code = f.read()
    except Exception as e:
        print("Error reading test.go:", e)
        sys.exit(1)

    try:
        # Parse the file using the Go parser
        parser = get_parser("go")
        tree = parser.parse(bytes(source_code, "utf8"))

        # Create CFG visitor and visit the tree
        visitor = GoCFGVisitor()
        visitor.visit(tree.root_node)
        visitor.postprocess_cfg()  # Clean up the CFG

        # Print detailed CFG information
        cfg = visitor.cfg
        print("\nCFG Analysis for Go code")
        print("-" * 50)
        print(f"Function name: {cfg.function_name}")
        print(f"Total nodes: {len(cfg.nodes)}")
        print(f"Entry nodes: {cfg.entry_node_ids}")
        print(f"Exit nodes: {cfg.exit_node_ids}\n")

        print("Node details:")
        print("-" * 50)
        for node_id, node in sorted(cfg.nodes.items()):
            print(f"\nNode {node_id} ({node.node_type})")
            print(f"  Text: {node.source_text}")
            print(f"  Predecessors: {sorted(node.predecessors)}")
            print(f"  Successors: {sorted(node.successors)}")
            if node.edge_labels:
                print(f"  Edge labels: {node.edge_labels}")
            if node.metadata:
                if node.metadata.variable_definitions:
                    print(
                        f"  Definitions: {sorted(node.metadata.variable_definitions)}"
                    )
                if node.metadata.variable_uses:
                    print(f"  Uses: {sorted(node.metadata.variable_uses)}")

        # Generate visualization
        output_file = "go_cfg.png"
        visualize_cfg(cfg, output_file)
        print(f"\nCFG visualization saved to: {output_file}")

    except Exception as e:
        print("Error generating CFG:", str(e))
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
