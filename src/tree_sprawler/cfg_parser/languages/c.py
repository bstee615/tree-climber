"""
Control Flow Graph (CFG) Generator Framework using py-tree-sitter for C language.
This framework uses the visitor pattern with depth-first traversal to build CFGs.
"""

from tree_sitter import Node

from tree_sprawler.cfg_parser.ast_utils import get_source_text
from tree_sprawler.cfg_parser.cfg_types import CFGTraversalResult, NodeType
from tree_sprawler.cfg_parser.cfg_visitor import CFGVisitor


class CCFGVisitor(CFGVisitor):
    """C-specific CFG visitor implementation"""

    def is_linear_statement(self, node: Node) -> bool:
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

    def visit_comment(self, node: Node) -> None:
        """Skip comment nodes entirely"""
        # Return None to indicate that this node should be ignored
        return None

    def visit_expression_statement(self, node: Node) -> CFGTraversalResult:
        return self.visit_linear_statement(node)

    def visit_declaration(self, node: Node) -> CFGTraversalResult:
        return self.visit_linear_statement(node)

    def visit_linear_statement(self, node: Node) -> CFGTraversalResult:
        # If the node is a linear statement, create a statement node
        node_id = self.cfg.create_node(NodeType.STATEMENT, node, get_source_text(node))
        return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

    def visit_function_definition(self, node: Node) -> CFGTraversalResult:
        """Visit a function definition"""
        # Find function name and body
        function_name = ""
        body_node = None

        for child in node.children:
            if child.type == "function_declarator":
                # Extract function name
                for subchild in child.children:
                    if subchild.type == "identifier":
                        function_name = get_source_text(subchild)
                        break
            elif child.type == "compound_statement":
                body_node = child

        self.cfg.function_name = function_name

        # Create entry node
        entry_id = self.cfg.create_node(NodeType.ENTRY, source_text=function_name)
        self.cfg.entry_node_ids.append(entry_id)
        self.context.push_entry(entry_id)
        self.context.register_function_definition(entry_id, function_name)

        # Create exit node
        exit_id = self.cfg.create_node(NodeType.EXIT, source_text=function_name)
        self.cfg.exit_node_ids.append(exit_id)
        self.context.push_exit(exit_id)

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

        self.context.pop_entry()
        self.context.pop_exit()

        return CFGTraversalResult(entry_node_id=entry_id, exit_node_ids=[exit_id])

    def visit_compound_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a compound statement (block)"""
        first_entry = None
        current_exits = []

        # Process each statement in the block
        for child in node.children:
            # Skip braces and comments
            if child.type in ["{", "}"] or child.type == "comment":
                continue

            # Visit each child
            child_result = self.visit(child)

            # Skip if the child returns None (comments or empty nodes)
            if not child_result:
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
            placeholder_id = self.cfg.create_node(
                NodeType.STATEMENT, source_text="empty block"
            )
            first_entry = placeholder_id
            current_exits = [placeholder_id]

        return CFGTraversalResult(
            entry_node_id=first_entry, exit_node_ids=current_exits
        )

    def visit_if_statement(self, node: Node) -> CFGTraversalResult:
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

        # Create condition node with actual condition text
        if condition_node:
            condition_text = get_source_text(condition_node)
            cond_id = self.cfg.create_node(
                NodeType.CONDITION, condition_node, condition_text
            )
        else:
            cond_id = self.cfg.create_node(
                NodeType.CONDITION, source_text="COND: if stmt"
            )

        exit_nodes = []

        # Create an explicit exit node for the if statement
        if_exit_id = self.cfg.create_node(NodeType.EXIT, source_text="EXIT: if stmt")

        # Process then branch with "true" label
        if then_stmt:
            then_result = self.visit(then_stmt)
            self.cfg.add_edge(cond_id, then_result.entry_node_id, "true")

            # Connect then-branch exits to the if's exit node
            for exit_node in then_result.exit_node_ids:
                self.cfg.add_edge(exit_node, if_exit_id)

        # Process else branch with "false" label
        if else_stmt:
            else_result = self.visit(else_stmt)
            self.cfg.add_edge(cond_id, else_result.entry_node_id, "false")

            # Connect else-branch exits to the if's exit node
            for exit_node in else_result.exit_node_ids:
                self.cfg.add_edge(exit_node, if_exit_id)
        else:
            # No else branch, direct false path to the exit node
            self.cfg.add_edge(cond_id, if_exit_id, "false")

        # The if statement has a single exit node now
        exit_nodes = [if_exit_id]

        return CFGTraversalResult(entry_node_id=cond_id, exit_node_ids=exit_nodes)

    def visit_while_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a while loop"""
        condition_node = None
        body_stmt = None

        # Parse while statement
        for child in node.children:
            if child.type == "parenthesized_expression":
                condition_node = child
            elif child.type != "while":
                body_stmt = child

        # Create loop header (condition) with actual condition text
        if condition_node:
            condition_text = get_source_text(condition_node)
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER, condition_node, condition_text
            )
        else:
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER, source_text="COND: while loop"
            )

        # Create exit node for the loop
        loop_exit_id = self.cfg.create_node(
            NodeType.EXIT, source_text="EXIT: while loop"
        )

        # Set up loop context
        self.context.push_loop_context(loop_exit_id, loop_header_id)

        # Process loop body
        if body_stmt:
            body_result = self.visit(body_stmt)
            # Connect condition to body entry with "true" label
            self.cfg.add_edge(loop_header_id, body_result.entry_node_id, "true")
            # Connect body exits back to condition
            for body_exit in body_result.exit_node_ids:
                self.cfg.add_edge(body_exit, loop_header_id)

        # Connect condition to exit (false branch) with "false" label
        self.cfg.add_edge(loop_header_id, loop_exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=loop_header_id, exit_node_ids=[loop_exit_id]
        )

    def visit_for_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a for loop"""
        body_stmt = None
        init_expr = None
        condition_expr = None
        update_expr = None

        # Parse for statement to find the different components
        for child in node.children:
            if child.type == "for":
                continue
            elif child.type == "(" or child.type == ")":
                continue
            elif (
                child.type == "compound_statement"
                or child.type == "expression_statement"
            ):
                body_stmt = child
            elif child.type == ";":
                continue
            else:
                # The for loop format is: for (init; condition; update) body
                # We need to find these three components based on their position
                if init_expr is None:
                    init_expr = child
                elif condition_expr is None:
                    condition_expr = child
                elif update_expr is None:
                    update_expr = child

        # Create initialization node with actual initialization code
        init_text = get_source_text(init_expr) if init_expr else "INIT: for loop"
        init_id = self.cfg.create_node(NodeType.STATEMENT, init_expr, init_text)

        # Create condition node with actual condition code
        condition_text = (
            get_source_text(condition_expr) if condition_expr else "for loop"
        )
        condition_id = self.cfg.create_node(
            NodeType.LOOP_HEADER, condition_expr, condition_text
        )

        # Create update node with actual update code
        update_text = get_source_text(update_expr) if update_expr else "for update"
        update_id = self.cfg.create_node(NodeType.STATEMENT, update_expr, update_text)

        # Create exit node
        exit_id = self.cfg.create_node(NodeType.EXIT, source_text="EXIT: for loop")

        # Connect init to condition
        self.cfg.add_edge(init_id, condition_id)

        # Set up loop context
        self.context.push_loop_context(exit_id, update_id)

        # Process body
        if body_stmt:
            body_result = self.visit(body_stmt)
            # Connect condition to body entry with "true" label
            self.cfg.add_edge(condition_id, body_result.entry_node_id, "true")
            # Connect body exits to update
            for body_exit in body_result.exit_node_ids:
                self.cfg.add_edge(body_exit, update_id)

        # Connect update back to condition
        self.cfg.add_edge(update_id, condition_id)

        # Connect condition to exit (false branch) with "false" label
        self.cfg.add_edge(condition_id, exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=init_id, exit_node_ids=[exit_id])

    def visit_break_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a break statement"""
        break_id = self.cfg.create_node(NodeType.BREAK, node, get_source_text(node))

        # Connect to break target if available
        break_target = self.context.get_break_target()
        if break_target is not None:
            self.cfg.add_edge(break_id, break_target)

            # The break statement terminates the current control flow
            # No normal successors, and an empty exit node list indicates
            # that control flow doesn't continue within the current block

        return CFGTraversalResult(
            entry_node_id=break_id, exit_node_ids=[]
        )  # Break statements don't have normal successors within their context

    def visit_continue_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a continue statement"""
        continue_id = self.cfg.create_node(
            NodeType.CONTINUE, node, get_source_text(node)
        )

        # Connect to continue target if available
        continue_target = self.context.get_continue_target()
        if continue_target is not None:
            self.cfg.add_edge(continue_id, continue_target)

        return CFGTraversalResult(
            entry_node_id=continue_id, exit_node_ids=[]
        )  # Continue statements don't have normal successors

    def visit_return_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a return statement"""
        return_id = self.cfg.create_node(NodeType.RETURN, node, get_source_text(node))

        # Connect to function exit
        if self.cfg.exit_node_ids:
            self.cfg.add_edge(return_id, self.cfg.exit_node_ids[-1])

        return CFGTraversalResult(
            entry_node_id=return_id, exit_node_ids=[]
        )  # Return statements don't have normal successors

    def visit_do_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a do-while loop"""
        condition_node = None
        body_stmt = None

        # Parse do-while statement
        for child in node.children:
            if child.type == "parenthesized_expression":
                condition_node = child
            elif child.type != "do" and child.type != "while" and child.type != ";":
                body_stmt = child

        # Create loop header (condition) with actual condition text
        if condition_node:
            condition_text = get_source_text(condition_node)
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER, condition_node, condition_text
            )
        else:
            loop_header_id = self.cfg.create_node(
                NodeType.LOOP_HEADER, source_text="COND: do-while loop"
            )

        # Create exit node for the loop
        loop_exit_id = self.cfg.create_node(
            NodeType.EXIT, source_text="EXIT: do-while loop"
        )

        # Create entry node for do-while loop
        do_entry_id = self.cfg.create_node(
            NodeType.ENTRY, source_text="ENTRY: do-while loop"
        )

        # Set up loop context for break/continue
        self.context.push_loop_context(loop_exit_id, loop_header_id)

        # Process loop body
        body_entry_id = None
        if body_stmt:
            body_result = self.visit(body_stmt)
            body_entry_id = body_result.entry_node_id

            # Connect entry node to body entry
            self.cfg.add_edge(do_entry_id, body_entry_id)

            # Connect body exits to condition
            for body_exit in body_result.exit_node_ids:
                self.cfg.add_edge(body_exit, loop_header_id)
        else:
            # Empty body, create a placeholder node
            body_entry_id = self.cfg.create_node(
                NodeType.STATEMENT, source_text="do-while body (empty)"
            )
            self.cfg.add_edge(do_entry_id, body_entry_id)
            self.cfg.add_edge(body_entry_id, loop_header_id)

        # Connect condition back to body entry with "true" label (looping back)
        self.cfg.add_edge(loop_header_id, body_entry_id, "true")

        # Connect condition to exit with "false" label
        self.cfg.add_edge(loop_header_id, loop_exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=do_entry_id, exit_node_ids=[loop_exit_id]
        )

    def visit_switch_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a switch statement"""
        condition_node = None
        body_node = None

        # Parse switch statement
        for child in node.children:
            if child.type == "parenthesized_expression":
                condition_node = child
            elif child.type == "compound_statement":
                body_node = child

        # Create switch head node with condition
        if condition_node:
            condition_text = get_source_text(condition_node)
            switch_head_id = self.cfg.create_node(
                NodeType.SWITCH_HEAD, condition_node, condition_text
            )
        else:
            switch_head_id = self.cfg.create_node(
                NodeType.SWITCH_HEAD, source_text="SWITCH"
            )

        # Create exit node for the switch
        switch_exit_id = self.cfg.create_node(NodeType.EXIT, source_text="EXIT: switch")

        # Set up switch context for break statements
        self.context.push_switch_context(switch_exit_id, switch_head_id)

        # Process switch body, which should contain case statements
        if body_node:
            body_result = self.visit(body_node)

            # Connect switch head to body entry
            # Note: We don't add edge labels here as the individual case statements
            # will connect to the switch head with appropriate case value labels
            self.cfg.add_edge(switch_head_id, body_result.entry_node_id)

            # Connect body exits to switch exit
            for exit_node in body_result.exit_node_ids:
                self.cfg.add_edge(exit_node, switch_exit_id)
        else:
            # Empty switch, connect head directly to exit
            self.cfg.add_edge(switch_head_id, switch_exit_id)

        # Clean up switch context
        self.context.pop_switch_context()

        return CFGTraversalResult(
            entry_node_id=switch_head_id, exit_node_ids=[switch_exit_id]
        )

    def visit_case_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a case statement within a switch"""
        value_expr = None
        body_stmts = []

        # Parse case statement
        for child in node.children:
            if child.type != "case" and child.type != ":" and value_expr is None:
                value_expr = child
            elif child.type != "case" and child.type != ":" and value_expr is not None:
                body_stmts.append(child)
                # We don't break here since there may be multiple statements

        # Create case node with the case value
        if value_expr:
            value_text = get_source_text(value_expr)
            case_id = self.cfg.create_node(
                NodeType.CASE, value_expr, f"CASE: {value_text}"
            )
        else:
            value_text = "case"
            case_id = self.cfg.create_node(NodeType.CASE, source_text="CASE")

        # Connect case to switch head if available
        switch_head = self.context.get_switch_head()
        if switch_head is not None:
            # Add edge with case value as label
            value_label = value_text
            self.cfg.add_edge(switch_head, case_id, value_label)

        exit_nodes = [case_id]  # Default exit is case node itself for fall-through

        # Process all body statements in sequence if present
        if body_stmts:
            last_exits = [case_id]  # Start with the case node

            # Process each statement in the body sequentially
            for body_stmt in body_stmts:
                stmt_result = self.visit(body_stmt)
                if stmt_result:  # Make sure we got a valid result
                    # Connect last statement's exits to this statement's entry
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    # Update the current exits
                    last_exits = stmt_result.exit_node_ids

                    # If it's a break or other control flow statement (like return/goto)
                    if not last_exits:  # Empty exit nodes list
                        # No fall-through to the next case
                        exit_nodes = []
                        break

            # If we went through all statements and still have exit nodes,
            # those become the exit nodes for the whole case
            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=case_id, exit_node_ids=exit_nodes)

    def visit_default_case(self, node: Node) -> CFGTraversalResult:
        """Visit a default case within a switch"""
        body_stmts = []

        # Parse default statement
        for child in node.children:
            if child.type != "default" and child.type != ":":
                body_stmts.append(child)

        # Create default case node
        default_id = self.cfg.create_node(NodeType.DEFAULT, source_text="DEFAULT")

        # Connect default to switch head if available
        switch_head = self.context.get_switch_head()
        if switch_head is not None:
            self.cfg.add_edge(switch_head, default_id, "default")

        exit_nodes = [default_id]  # Default exit is the default node itself

        # Process all body statements in sequence if present
        if body_stmts:
            last_exits = [default_id]  # Start with the default node

            # Process each statement in the body sequentially
            for body_stmt in body_stmts:
                stmt_result = self.visit(body_stmt)
                if stmt_result:  # Make sure we got a valid result
                    # Connect last statement's exits to this statement's entry
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    # Update the current exits
                    last_exits = stmt_result.exit_node_ids

                    # If it's a break or other control flow statement (like return/goto)
                    if not last_exits:  # Empty exit nodes list
                        # No fall-through after the default case
                        exit_nodes = []
                        break

            # If we went through all statements and still have exit nodes,
            # those become the exit nodes for the default case
            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=default_id, exit_node_ids=exit_nodes)

    def visit_labeled_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a labeled statement - target for goto statements"""
        label_name = None
        body_stmt = None

        # Parse labeled statement
        for child in node.children:
            if child.type == "statement_identifier":
                label_name = get_source_text(child)
            elif child.type != ":" and label_name is not None:
                body_stmt = child
                break

        # Create label node
        label_id = self.cfg.create_node(
            NodeType.LABEL, source_text=label_name or "LABEL"
        )

        # Register label in context
        if label_name:
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
        target_label = None

        # Parse goto statement to find target label
        for child in node.children:
            if child.type == "statement_identifier":
                target_label = get_source_text(child)
                break

        # Create goto node
        goto_id = self.cfg.create_node(NodeType.GOTO, node, target_label or "GOTO")

        # Try to connect to label if it exists
        if target_label:
            target_id = self.context.add_goto_ref(target_label, goto_id)
            if target_id:
                # If label already defined, connect goto to label
                self.cfg.add_edge(goto_id, target_id)

        # Goto statements don't have normal successors (control flow is transferred)
        return CFGTraversalResult(entry_node_id=goto_id, exit_node_ids=[])
