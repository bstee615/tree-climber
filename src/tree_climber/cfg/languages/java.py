"""
Control Flow Graph (CFG) Generator Framework using py-tree-sitter for Java language.
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


class JavaCFGVisitor(CFGVisitor):
    """Java-specific CFG visitor implementation"""

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
        """If the node is a linear statement, create a statement node"""
        node_id = self.create_node(NodeType.STATEMENT, node, get_source_text(node))
        return CFGTraversalResult(entry_node_id=node_id, exit_node_ids=[node_id])

    # AST utilities
    def get_calls(self, ast_node: Node) -> List[str]:
        """Extract function calls under an AST node."""

        def process_call(node: Node) -> Optional[str]:
            if node.type == "method_invocation":
                # In Java, method calls are like: obj.method() or method()
                identifiers = []
                for child in node.children:
                    if child.type == "identifier":
                        identifiers.append(get_source_text(child))
                if len(identifiers) > 0:
                    # return ".".join(identifiers) # TODO handle object or package names
                    return identifiers[-1]
            return None

        return dfs(ast_node, process_call)

    def get_definitions(self, ast_node: Node) -> List[str]:
        """Extract variable definitions under an AST node."""

        def process_definition(node: Node) -> Optional[str]:
            if (
                node.type == "identifier"
                and node.parent
                and node.parent.type in ["enhanced_for_statement"]
            ):
                return get_source_text(node)
            if node.type == "variable_declarator":
                # Look for identifier in declarator
                for child in node.children:
                    if child.type == "identifier":
                        return get_source_text(child)
            elif node.type == "update_expression":
                # Look for identifier in declarator
                for child in node.children:
                    if child.type == "identifier":
                        return get_source_text(child)
            elif node.type == "assignment_expression":
                # Find the left side identifier
                left = node.children[0] if node.children else None
                if left and left.type == "identifier":
                    return get_source_text(left)
            return None

        return dfs(ast_node, process_definition)

    def get_uses(self, ast_node: Node) -> List[str]:
        """Extract variable uses under an AST node."""

        def process_use(node: Node) -> Optional[str]:
            if node.type == "identifier":
                # Skip identifiers in various contexts where they're not "uses"
                if node.parent:
                    if node.parent.type in [
                        "method_declaration",  # Function defs
                        "method_invocation",  # Function calls
                        "field_access",  # Method names in calls
                        "variable_declarator",  # Variable declarations
                        "parameter",  # Parameter declarations
                        "class_declaration",  # Class names
                    ]:
                        return None
                    if node.parent.type == "update_expression":
                        # Check if this is the target (left side) of the update
                        if node == node.parent.children[0]:
                            return get_source_text(node)
                    if node.parent.type == "assignment_expression":
                        # Check if this is the target (left side) of the assignment
                        if node == node.parent.children[0]:
                            if node.parent.children[1].type in ("-=", "+=", "*=", "/="):
                                # Compound assignment, treat as use
                                return get_source_text(node)
                            return None  # Simple assignment target, not a use
                return get_source_text(node)
            return None

        return dfs(ast_node, process_use)

    def is_linear_statement(self, node: Node) -> bool:
        """Check if a node represents a simple linear statement"""
        # Control flow statements that create branches or edges
        non_linear_types = [
            "if_statement",
            "for_statement",
            "enhanced_for_statement",  # Java's for-each loop
            "while_statement",
            "do_statement",
            "switch_statement",
            "break_statement",
            "continue_statement",
            "return_statement",
            "block",  # Java's equivalent of compound_statement
        ]

        # Check if node type isn't one of the non-linear types
        return node.type.endswith("_statement") and node.type not in non_linear_types

    # Basic visitor methods
    def visit_program(self, node: Node) -> CFGTraversalResult:
        """Visit the root program node"""
        first_entry = None
        last_exits = None
        for child in node.children:
            if child.type == "class_declaration":
                result = self.visit(child)
                if first_entry is None:
                    first_entry = result.entry_node_id
                last_exits = result.exit_node_ids

        assert (
            first_entry is not None
        ), "Translation unit must have at least one entry node"
        assert (
            last_exits is not None
        ), "Translation unit must have at least one exit node"
        return CFGTraversalResult(
            entry_node_id=first_entry,
            exit_node_ids=last_exits,
        )

    def visit_comment(self, node: Node) -> None:
        """Skip comment nodes entirely"""
        return None

    def visit_expression_statement(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_local_variable_declaration(self, node: Node) -> CFGTraversalResult:
        return self._visit_linear_statement(node)

    def visit_class_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a class declaration"""
        body = get_required_child_by_field_name(node, "body")
        return self.visit(body)

    def visit_class_body(self, node: Node) -> CFGTraversalResult:
        """Visit a class body"""
        first_entry = None
        last_exits = None
        for child in node.children:
            if not child.is_named or child.type.endswith("comment"):
                continue
            result = self.visit(child)
            if first_entry is None:
                first_entry = result.entry_node_id
            if last_exits is None:
                last_exits = result.exit_node_ids
        assert first_entry is not None, "Class body must have at least one entry node"
        assert last_exits is not None, "Class body must have at least one exit node"
        return CFGTraversalResult(entry_node_id=first_entry, exit_node_ids=last_exits)

    def visit_method_declaration(self, node: Node) -> CFGTraversalResult:
        """Visit a method declaration"""
        # Get components via named fields
        identifier = get_required_child_by_field_name(node, "name")
        body_node = get_required_child_by_field_name(node, "body")
        parameters = get_child_by_field_name(node, "parameters")  # This one is correct

        # Extract method name
        method_name = get_source_text(identifier)

        # Extract parameters list
        param_list = []
        if parameters:
            for param in parameters.children:
                if param.type == "formal_parameter":
                    param_identifier = get_required_child_by_field_name(param, "name")
                    param_list.append(get_source_text(param_identifier))

        # Find closing brace in body for exit node location
        closing_brace = None
        for child in body_node.children:
            if child.type == "}":
                closing_brace = child

        self.cfg.function_name = method_name

        # Create entry node with method name and parameters
        entry_id = self.create_node(
            NodeType.ENTRY, source_text=method_name, ast_node=identifier
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

        # Process method body
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
            if not child.is_named or child.type.endswith("_comment"):
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
        condition_node = get_required_child_by_field_name(node, "condition")
        then_stmt = get_required_child_by_field_name(node, "consequence")
        else_clause = get_child_by_field_name(node, "alternative")

        # Create condition node
        cond_id = self._create_condition_node(condition_node, NodeType.CONDITION)

        # Create an explicit exit node for the if statement
        if_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: if stmt")

        # Process then branch with "true" label
        self._create_body_node(then_stmt, cond_id, if_exit_id, edge_label="true")

        # Process else branch with "false" label
        if else_clause:
            self._create_body_node(else_clause, cond_id, if_exit_id, edge_label="false")
        else:
            # No else branch, direct false path to the exit node
            self.cfg.add_edge(cond_id, if_exit_id, "false")

        return CFGTraversalResult(entry_node_id=cond_id, exit_node_ids=[if_exit_id])

    def visit_while_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a while loop"""
        # Get components via named fields
        condition_node = get_required_child_by_field_name(node, "condition")
        body_stmt = get_required_child_by_field_name(node, "body")

        # Create loop header node
        loop_header_id = self._create_condition_node(
            condition_node, NodeType.LOOP_HEADER
        )

        # Create exit node for the loop
        loop_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: while loop")

        # Set up loop context
        self.context.push_loop_context(loop_exit_id, loop_header_id)

        # Process loop body
        self._create_body_node(
            body_stmt, loop_header_id, loop_header_id, edge_label="true"
        )

        # Connect condition to exit (false branch) with "false" label
        self.cfg.add_edge(loop_header_id, loop_exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=loop_header_id, exit_node_ids=[loop_exit_id]
        )

    def visit_do_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a do-while loop"""
        # Get components via named fields
        condition_node = get_required_child_by_field_name(node, "condition")
        body_stmt = get_required_child_by_field_name(node, "body")

        # Create loop header (condition) with actual condition text
        condition_text = get_source_text(condition_node)
        loop_header_id = self.create_node(
            NodeType.LOOP_HEADER, condition_node, condition_text
        )

        # Create exit node for the loop
        loop_exit_id = self.create_node(
            NodeType.EXIT, source_text="EXIT: do-while loop"
        )

        # Create entry node for do-while loop
        do_entry_id = self.create_node(
            NodeType.ENTRY, source_text="ENTRY: do-while loop"
        )

        # Set up loop context for break/continue
        self.context.push_loop_context(loop_exit_id, loop_header_id)

        # Process loop body
        body_result = self._create_body_node(body_stmt, do_entry_id, loop_header_id)
        body_entry_id = body_result.entry_node_id

        # Connect condition back to body entry with "true" label (looping back)
        self.cfg.add_edge(loop_header_id, body_entry_id, "true")

        # Connect condition to exit with "false" label
        self.cfg.add_edge(loop_header_id, loop_exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(
            entry_node_id=do_entry_id, exit_node_ids=[loop_exit_id]
        )

    def visit_for_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a for loop"""
        # Get components via named fields
        init = get_child_by_field_name(node, "init")  # Changed from 'init'
        condition = get_child_by_field_name(node, "condition")  # This is correct
        update = get_child_by_field_name(node, "update")  # This is correct
        body = get_required_child_by_field_name(node, "body")  # This is correct

        # Create entry node that represents the start of the loop
        entry_id = self.create_node(NodeType.ENTRY, source_text="FOR_LOOP_ENTRY")

        # Create initialization node with actual initialization code if present
        init_id = entry_id
        if init:
            init_text = get_source_text(init)
            init_id = self.create_node(NodeType.STATEMENT, init, init_text)
            # Connect entry to init if it exists
            if init_id != entry_id:
                self.cfg.add_edge(entry_id, init_id)

        # Create condition node if present
        if condition:
            condition_text = get_source_text(condition)
            condition_id = self.create_node(
                NodeType.LOOP_HEADER, condition, condition_text
            )
        else:
            # If no condition, create a true condition
            condition_id = self.create_node(NodeType.LOOP_HEADER, source_text="true")

        # Create update node with actual update code if present
        if update:
            update_text = get_source_text(update)
            update_id = self.create_node(NodeType.STATEMENT, update, update_text)
        else:
            # If no update, use condition node as update target for continue statements
            update_id = condition_id

        # Create exit node
        exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: for loop")

        # Connect init to condition
        self.cfg.add_edge(init_id, condition_id)

        # Set up loop context
        self.context.push_loop_context(exit_id, update_id)

        # Process body
        self._create_body_node(body, condition_id, update_id, edge_label="true")

        # Connect update back to condition
        self.cfg.add_edge(update_id, condition_id)

        # Connect condition to exit (false branch) with "false" label
        self.cfg.add_edge(condition_id, exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=init_id, exit_node_ids=[exit_id])

    def visit_enhanced_for_statement(self, node: Node) -> CFGTraversalResult:
        """Visit an enhanced for loop (for-each)"""
        # Get components via named fields
        variable = get_required_child_by_field_name(node, "name")  # Fixed previously
        iterable = get_required_child_by_field_name(node, "value")  # Fixed previously
        body = get_required_child_by_field_name(node, "body")

        # Create a synthetic condition checking for next element
        condition_text = f"hasNext({get_source_text(iterable)})"
        condition_id = self.create_node(NodeType.LOOP_HEADER, iterable, condition_text)

        # Create a synthetic node for element assignment
        element_text = f"{get_source_text(variable)} = next()"
        element_id = self.create_node(NodeType.STATEMENT, variable, element_text)

        # Create exit node
        exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: for-each loop")

        # Connect condition to variable assignment with "true" label
        self.cfg.add_edge(
            condition_id, element_id, "true"
        )  # Fixed variable name from assignment_id to element_id

        # Set up loop context using condition as continue target
        self.context.push_loop_context(exit_id, condition_id)

        # Process body
        self._create_body_node(body, element_id, condition_id)

        # Connect condition to exit with "false" label
        self.cfg.add_edge(condition_id, exit_id, "false")

        # Clean up loop context
        self.context.pop_loop_context()

        return CFGTraversalResult(entry_node_id=condition_id, exit_node_ids=[exit_id])

    def visit_break_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a break statement"""
        break_id = self.create_node(NodeType.BREAK, node, get_source_text(node))

        # Connect to break target if available
        break_target = self.context.get_break_target()
        assert break_target is not None, "Break statement must have a target"
        self.cfg.add_edge(break_id, break_target)

        # Break statements don't have normal successors within their context
        return CFGTraversalResult(entry_node_id=break_id, exit_node_ids=[])

    def visit_continue_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a continue statement"""
        continue_id = self.create_node(NodeType.CONTINUE, node, get_source_text(node))

        # Connect to continue target if available
        continue_target = self.context.get_continue_target()
        assert continue_target is not None, "Continue statement must have a target"
        self.cfg.add_edge(continue_id, continue_target)

        # Continue statements don't have normal successors
        return CFGTraversalResult(entry_node_id=continue_id, exit_node_ids=[])

    def visit_return_statement(self, node: Node) -> CFGTraversalResult:
        """Visit a return statement"""
        return_id = self.create_node(NodeType.RETURN, node, get_source_text(node))

        # Connect to function exit
        assert (
            len(self.cfg.exit_node_ids) > 0
        ), "Return statement must have an exit node"
        self.cfg.add_edge(return_id, self.cfg.exit_node_ids[-1])

        # Return statements don't have normal successors
        return CFGTraversalResult(entry_node_id=return_id, exit_node_ids=[])

    def visit_switch_expression(self, node: Node) -> CFGTraversalResult:
        """Visit a switch statement"""
        expression = get_required_child_by_field_name(
            node, "condition"
        )  # Fixed previously
        body = get_required_child_by_field_name(node, "body")

        # Create switch head node with expression text
        switch_head_id = self._create_condition_node(expression, NodeType.SWITCH_HEAD)

        # Create exit node for the switch
        switch_exit_id = self.create_node(NodeType.EXIT, source_text="EXIT: switch")

        # Set up switch context for break statements
        self.context.push_switch_context(switch_exit_id, switch_head_id)

        # Process switch body, which should contain case statements
        self._create_body_node(body, switch_head_id, switch_exit_id)

        # Clean up switch context
        self.context.pop_switch_context()

        return CFGTraversalResult(
            entry_node_id=switch_head_id, exit_node_ids=[switch_exit_id]
        )

    def visit_switch_block_statement_group(self, node: Node) -> CFGTraversalResult:
        """Visit a switch case block"""
        # First nodes should be the case/default labels
        case_labels = []
        statements = []
        for child in node.children:
            if child.type in ("switch_label", "default_label"):
                case_labels.append(child)
            else:
                statements.append(child)

        if not case_labels:
            # Create an empty placeholder node for invalid switch blocks
            placeholder_id = self.create_node(
                NodeType.STATEMENT, source_text="empty switch block"
            )
            return CFGTraversalResult(
                entry_node_id=placeholder_id, exit_node_ids=[placeholder_id]
            )

        first_label = case_labels[0]
        case_id = None
        value_text = None

        # Process case label
        if first_label.type == "switch_label":
            # expression = next(child for child in first_label.children if child.is_named)
            expression = next(
                child
                for child in first_label.children
                if not child.type.endswith("_comment") and child.type != "case"
            )
            value_text = get_source_text(expression)
            case_id = self.create_node(
                NodeType.CASE, first_label, f"CASE: {value_text}"
            )
        else:  # default label
            value_text = "default"
            case_id = self.create_node(NodeType.CASE, first_label, "DEFAULT")

        # Connect case to switch head if available
        switch_head = self.context.get_switch_head()
        if switch_head is not None:
            self.cfg.add_edge(switch_head, case_id, value_text)

        exit_nodes = [case_id]  # Default exit is case node itself for fall-through

        # Process all statements in sequence
        if statements:
            last_exits = [case_id]  # Start with the case node

            for stmt in statements:
                if not stmt.is_named or stmt.type.endswith("comment"):
                    continue  # Skip unnamed nodes and comments
                stmt_result = self.visit(stmt)
                if stmt_result:  # Make sure we got a valid result
                    # Connect last statement's exits to this statement's entry
                    for exit_id in last_exits:
                        self.cfg.add_edge(exit_id, stmt_result.entry_node_id)

                    # Update the current exits
                    last_exits = stmt_result.exit_node_ids

                    # If it's a break or other control flow statement
                    if not last_exits:  # Empty exit nodes list
                        # No fall-through to the next case
                        exit_nodes = []
                        break

            # If we went through all statements and still have exit nodes,
            # those become the exit nodes for the whole case
            if last_exits:
                exit_nodes = last_exits

        return CFGTraversalResult(entry_node_id=case_id, exit_node_ids=exit_nodes)


def main():
    """Main function to test Java CFG generation"""
    import os
    import sys

    from tree_sitter_languages import get_parser

    from tree_climber.cfg.visualization import visualize_cfg

    # Read the test file
    try:
        test_file = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "test",
            "test.java",
        )
        with open(test_file, "r") as f:
            source_code = f.read()
    except Exception as e:
        print("Error reading test.java:", e)
        sys.exit(1)

    try:
        # Parse the file using the Java parser
        parser = get_parser("java")
        tree = parser.parse(bytes(source_code, "utf8"))

        # Create CFG visitor and visit the tree
        visitor = JavaCFGVisitor()
        visitor.visit(tree.root_node)
        visitor.postprocess_cfg()  # Clean up the CFG

        # Print detailed CFG information
        cfg = visitor.cfg
        print("\nCFG Analysis for Java code")
        print("-" * 50)
        print(f"Method name: {cfg.function_name}")
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
        output_file = "java_cfg.png"
        visualize_cfg(cfg, output_file)
        print(f"\nCFG visualization saved to: {output_file}")

    except Exception as e:
        print("Error generating CFG:", str(e))
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
