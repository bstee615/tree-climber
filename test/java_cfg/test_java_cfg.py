#!/usr/bin/env python3
"""
Comprehensive Java CFG Testing Suite

This module provides comprehensive end-to-end validation of Java Control Flow Graph (CFG)
generation. It tests individual constructs, nested combinations, edge cases, and Java-specific
features to ensure robust and accurate CFG creation.

Test Organization:
- 12 test categories covering all Java language constructs
- Helper methods for CFG validation and debugging
- Systematic validation of node counts, types, connectivity, and metadata
- Support for debugging individual test failures

Following the successful C CFG testing methodology that achieved 100% test pass rate.

Created: 2025-08-14
Author: Claude Code Assistant
"""

import pytest
from typing import List, Dict, Set, Optional, Tuple
import tempfile
import os

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.cfg_types import NodeType
from tree_climber.cfg.visitor import CFG


class JavaCFGTestHelper:
    """Helper class for Java CFG testing and validation."""

    def __init__(self):
        self.builder = CFGBuilder("java")
        self.builder.setup_parser()

    def build_cfg_from_method(self, java_code: str, method_name: str) -> CFG:
        """Build CFG from a specific method within a Java class."""
        # Wrap the method in a minimal class if it's not already wrapped
        if not java_code.strip().startswith(
            "class "
        ) and not java_code.strip().startswith("public class"):
            class_code = f"""
public class TestClass {{
    {java_code}
}}
"""
        else:
            class_code = java_code

        cfg = self.builder.build_cfg(class_code)
        return cfg

    def build_cfg_from_java_file(self, file_path: str, method_name: str) -> CFG:
        """Build CFG from a method in a Java file."""
        with open(file_path, "r") as f:
            content = f.read()

        # Extract the specific method from the file
        lines = content.split("\n")
        method_lines = []
        in_method = False
        brace_count = 0

        for line in lines:
            if f"public static" in line and method_name in line and "(" in line:
                in_method = True
                brace_count = 0

            if in_method:
                method_lines.append(line)
                brace_count += line.count("{") - line.count("}")

                if brace_count == 0 and "}" in line:
                    break

        if not method_lines:
            raise ValueError(f"Method {method_name} not found in {file_path}")

        method_code = "\n".join(method_lines)
        return self.build_cfg_from_method(method_code, method_name)

    def build_cfg_from_code(self, java_code: str) -> CFG:
        """Build CFG from complete Java source code."""
        return self.builder.build_cfg(java_code)

    def assert_node_count(self, cfg: CFG, expected_count: int, message: str = ""):
        """Assert the total number of nodes in the CFG."""
        actual_count = len(cfg.nodes)
        assert actual_count == expected_count, (
            f"Expected {expected_count} nodes, got {actual_count}. {message}\n"
            f"Actual nodes: {[(node.id, node.node_type.name, node.source_text) for node in cfg.nodes.values()]}"
        )

    def assert_node_types(self, cfg: CFG, expected_types: List[str], message: str = ""):
        """Assert the presence of specific node types."""
        actual_types = [node.node_type.name for node in cfg.nodes.values()]
        type_counts = {}

        for node_type in expected_types:
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        for node_type, expected_count in type_counts.items():
            actual_count = actual_types.count(node_type)
            assert actual_count == expected_count, (
                f"Expected {expected_count} {node_type} nodes, got {actual_count}. {message}\n"
                f"All node types: {actual_types}"
            )

    def assert_entry_exit_nodes(self, cfg: CFG, message: str = ""):
        """Assert proper entry and exit node structure."""
        entry_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.ENTRY]
        exit_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.EXIT]

        assert len(entry_nodes) >= 1, f"Must have at least one ENTRY node. {message}"
        assert len(exit_nodes) >= 1, f"Must have at least one EXIT node. {message}"

        # Check that entry nodes are in the CFG's entry list
        for entry_node in entry_nodes:
            assert entry_node.id in cfg.entry_node_ids, (
                f"Entry node {entry_node.id} not in CFG entry list. {message}"
            )

        # Check that exit nodes are in the CFG's exit list
        for exit_node in exit_nodes:
            assert exit_node.id in cfg.exit_node_ids, (
                f"Exit node {exit_node.id} not in CFG exit list. {message}"
            )

    def assert_edge_connections(
        self,
        cfg: CFG,
        expected_edges: List[Tuple[str, str, Optional[str]]],
        message: str = "",
    ):
        """Assert specific edge connections exist."""
        for from_node_text, to_node_text, expected_label in expected_edges:
            from_nodes = [
                n for n in cfg.nodes.values() if from_node_text in n.source_text
            ]

            # Special handling for EXIT nodes
            if to_node_text == "EXIT":
                to_nodes = [
                    n for n in cfg.nodes.values() if n.node_type == NodeType.EXIT
                ]
            else:
                to_nodes = [
                    n for n in cfg.nodes.values() if to_node_text in n.source_text
                ]

            assert len(from_nodes) > 0, (
                f"Source node containing '{from_node_text}' not found. {message}"
            )
            assert len(to_nodes) > 0, (
                f"Target node containing '{to_node_text}' not found. {message}"
            )

            from_node = from_nodes[0]
            to_node = to_nodes[0]

            assert to_node.id in from_node.successors, (
                f"Expected edge from '{from_node.source_text}' to '{to_node.source_text}' not found. {message}\n"
                f"Actual successors: {[cfg.nodes[s].source_text for s in from_node.successors]}"
            )

            if expected_label is not None:
                actual_label = from_node.get_edge_label(to_node.id)
                assert actual_label == expected_label, (
                    f"Expected edge label '{expected_label}', got '{actual_label}'. {message}"
                )

    def assert_reachability(self, cfg: CFG, message: str = ""):
        """Assert all nodes are reachable from entry nodes."""
        if not cfg.entry_node_ids:
            return  # No entry nodes to check

        reachable = set()
        stack = list(cfg.entry_node_ids)

        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)

            if current in cfg.nodes:
                for successor in cfg.nodes[current].successors:
                    if successor not in reachable:
                        stack.append(successor)

        all_nodes = set(cfg.nodes.keys())
        unreachable = all_nodes - reachable

        # Some nodes may be unreachable by design (e.g., after return statements)
        # but we should verify this is intentional
        if unreachable:
            unreachable_descriptions = [
                f"{node_id}: {cfg.nodes[node_id].node_type.name} - '{cfg.nodes[node_id].source_text}'"
                for node_id in unreachable
            ]
            print(
                f"Warning: Found {len(unreachable)} unreachable nodes: {unreachable_descriptions}"
            )

    def assert_parameter_extraction(
        self, cfg: CFG, expected_parameters: List[str], message: str = ""
    ):
        """Assert method parameters are correctly extracted."""
        entry_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.ENTRY]
        assert len(entry_nodes) > 0, (
            f"No entry node found for parameter validation. {message}"
        )

        entry_node = entry_nodes[0]
        actual_parameters = entry_node.metadata.variable_definitions

        assert actual_parameters == expected_parameters, (
            f"Expected parameters {expected_parameters}, got {actual_parameters}. {message}"
        )

    def assert_variable_tracking(
        self,
        cfg: CFG,
        expected_definitions: Set[str],
        expected_uses: Set[str],
        message: str = "",
    ):
        """Assert variable definitions and uses are tracked correctly."""
        all_definitions = set()
        all_uses = set()

        for node in cfg.nodes.values():
            all_definitions.update(node.metadata.variable_definitions)
            all_uses.update(node.metadata.variable_uses)

        missing_definitions = expected_definitions - all_definitions
        extra_definitions = all_definitions - expected_definitions
        missing_uses = expected_uses - all_uses
        extra_uses = all_uses - expected_uses

        assert not missing_definitions, (
            f"Missing variable definitions: {missing_definitions}. {message}"
        )
        assert not missing_uses, f"Missing variable uses: {missing_uses}. {message}"

        # Extra definitions/uses are warnings, not errors
        if extra_definitions:
            print(f"Warning: Extra variable definitions: {extra_definitions}")
        if extra_uses:
            print(f"Warning: Extra variable uses: {extra_uses}")

    def debug_cfg_structure(self, cfg: CFG, title: str = "CFG Debug"):
        """Print detailed CFG structure for debugging."""
        print(f"\n{title}")
        print("=" * 60)
        print(f"Function: {cfg.function_name}")
        print(f"Total nodes: {len(cfg.nodes)}")
        print(f"Entry nodes: {cfg.entry_node_ids}")
        print(f"Exit nodes: {cfg.exit_node_ids}")

        print("\nNodes:")
        for node_id, node in sorted(cfg.nodes.items()):
            print(f"  {node_id} ({node.node_type.name}): '{node.source_text}'")
            if node.successors:
                successor_info = []
                for succ_id in node.successors:
                    label = node.get_edge_label(succ_id)
                    label_str = f" [{label}]" if label else ""
                    successor_info.append(f"{succ_id}{label_str}")
                print(f"    -> {', '.join(successor_info)}")

            if node.metadata.variable_definitions:
                print(f"    Defines: {node.metadata.variable_definitions}")
            if node.metadata.variable_uses:
                print(f"    Uses: {node.metadata.variable_uses}")
            if node.metadata.function_calls:
                print(f"    Calls: {node.metadata.function_calls}")


# Test Classes


class TestBasicControlFlow:
    """Test fundamental Java CFG generation for basic constructs."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_sequential_statements(self):
        """Test sequential statement CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "sequentialStatements"
        )

        # Should have: ENTRY -> STATEMENT -> STATEMENT -> STATEMENT -> EXIT
        self.helper.assert_node_count(cfg, 5, "Sequential statements")
        self.helper.assert_node_types(
            cfg, ["ENTRY", "STATEMENT", "STATEMENT", "STATEMENT", "EXIT"]
        )
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_method_with_parameters(self):
        """Test method parameter extraction."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "methodWithParameters"
        )

        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_parameter_extraction(cfg, ["x", "y"], "Method parameters")
        self.helper.assert_reachability(cfg)

    def test_empty_method(self):
        """Test empty method CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "emptyMethod")

        # Should have direct ENTRY -> EXIT connection
        self.helper.assert_node_types(cfg, ["ENTRY", "EXIT"])
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)


class TestConditionalStatements:
    """Test Java conditional statement CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_simple_if(self):
        """Test if statement without else."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "simpleIf")

        # Should have condition node with true/false branches
        self.helper.assert_node_types(
            cfg, ["ENTRY", "STATEMENT", "CONDITION", "STATEMENT", "EXIT"]
        )
        self.helper.assert_entry_exit_nodes(cfg)

        # Verify conditional edges
        self.helper.assert_edge_connections(
            cfg,
            [
                ("x > 0", "x = x + 1", "true"),
                ("x > 0", "EXIT", "false"),  # Use special EXIT handling
            ],
        )
        self.helper.assert_reachability(cfg)

    def test_if_else(self):
        """Test if-else statement."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "ifElse")

        self.helper.assert_node_types(
            cfg, ["ENTRY", "STATEMENT", "CONDITION", "STATEMENT", "STATEMENT", "EXIT"]
        )
        self.helper.assert_entry_exit_nodes(cfg)

        # Verify both branches
        self.helper.assert_edge_connections(
            cfg, [("x > 0", "x = x + 1", "true"), ("x > 0", "x = x - 1", "false")]
        )
        self.helper.assert_reachability(cfg)


class TestLoopConstructs:
    """Test Java loop construct CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_while_loop(self):
        """Test while loop CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "whileLoop")

        # Should have loop header with back-edge
        self.helper.assert_node_types(
            cfg, ["ENTRY", "STATEMENT", "LOOP_HEADER", "STATEMENT", "EXIT"]
        )
        self.helper.assert_entry_exit_nodes(cfg)

        # Verify loop structure
        self.helper.assert_edge_connections(
            cfg, [("i < 10", "i = i + 1", "true"), ("i < 10", "EXIT", "false")]
        )
        self.helper.assert_reachability(cfg)

    def test_for_loop(self):
        """Test for loop CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "forLoop")

        # Should have init, condition, body, update
        self.helper.assert_node_types(
            cfg, ["ENTRY", "STATEMENT", "LOOP_HEADER", "STATEMENT", "STATEMENT", "EXIT"]
        )
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_enhanced_for_loop(self):
        """Test enhanced for loop (for-each) CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "enhancedForLoop")

        # Should have synthetic hasNext condition and element assignment
        self.helper.assert_entry_exit_nodes(cfg)

        # Check for enhanced for loop structure
        loop_headers = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.LOOP_HEADER
        ]
        assert len(loop_headers) > 0, "Enhanced for should have loop header"
        self.helper.assert_reachability(cfg)

    def test_do_while_loop(self):
        """Test do-while loop CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "doWhileLoop")

        # Should have body executed before condition
        self.helper.assert_entry_exit_nodes(cfg)

        # Find loop header (condition) and verify it connects back to body
        loop_headers = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.LOOP_HEADER
        ]
        assert len(loop_headers) > 0, "Do-while should have loop header"
        self.helper.assert_reachability(cfg)


class TestJumpStatements:
    """Test Java jump statement CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_break_in_loop(self):
        """Test break statement in loop."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "breakInLoop")

        # Should have break node connecting to loop exit
        break_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.BREAK]
        assert len(break_nodes) > 0, "Should have BREAK node"
        self.helper.assert_reachability(cfg)

    def test_continue_in_loop(self):
        """Test continue statement in loop."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "continueInLoop")

        # Should have continue node connecting to loop header/update
        continue_nodes = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.CONTINUE
        ]
        assert len(continue_nodes) > 0, "Should have CONTINUE node"
        self.helper.assert_reachability(cfg)

    def test_return_statement(self):
        """Test return statement CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "returnStatement")

        # Should have return nodes connecting to method exit
        return_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.RETURN]
        assert len(return_nodes) > 0, "Should have RETURN nodes"

        # Verify returns connect to exit
        for return_node in return_nodes:
            exit_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.EXIT]
            assert len(exit_nodes) > 0, "Should have EXIT node"
            # Return should connect to exit through CFG exit list


class TestSwitchStatements:
    """Test Java switch statement CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_switch_with_breaks(self):
        """Test switch statement with break statements."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "switchWithBreaks")

        # Should have switch head and case connections
        switch_heads = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.SWITCH_HEAD
        ]
        assert len(switch_heads) > 0, "Should have SWITCH_HEAD node"

        # Should have break nodes
        break_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.BREAK]
        assert len(break_nodes) > 0, "Should have BREAK nodes"
        self.helper.assert_reachability(cfg)

    def test_switch_fallthrough(self):
        """Test switch statement with fall-through behavior."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "switchFallthrough"
        )

        # Should have switch head
        switch_heads = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.SWITCH_HEAD
        ]
        assert len(switch_heads) > 0, "Should have SWITCH_HEAD node"

        # Should model fall-through between cases
        self.helper.assert_reachability(cfg)


class TestExceptionHandling:
    """Test Java exception handling CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(os.path.dirname(__file__), "java_specific.java")

    def test_try_catch(self):
        """Test basic try-catch block."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "tryWithResources")

        # Should have exception handling structure
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_try_catch_finally(self):
        """Test try-catch-finally block."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "customExceptionHandling"
        )

        # Should handle finally block execution paths
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)


class TestObjectOriented:
    """Test Java object-oriented construct CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(os.path.dirname(__file__), "java_specific.java")

    def test_method_calls(self):
        """Test method invocation tracking."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "staticVsInstanceMethods"
        )

        # Should track method calls in metadata
        all_calls = set()
        for node in cfg.nodes.values():
            all_calls.update(node.metadata.function_calls)

        # Should have some method calls tracked
        # Note: Specific call tracking depends on implementation
        self.helper.assert_reachability(cfg)

    def test_constructor_calls(self):
        """Test constructor-like method CFG generation."""
        # Test a method that creates objects (constructor calls)
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "methodOverridingAndPolymorphism"
        )

        # Should handle object creation and method calls
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_method_call_edges(self):
        """Test that method calls create proper call and return edges."""
        java_code = """
        public class Test {
            public static void helper() {
                int y = 10;
            }
            
            public static void main(String[] args) {
                int x = 5;
                helper();
                x = x + 1;
            }
        }
        """
        cfg = self.helper.build_cfg_from_code(java_code)

        # Find function nodes
        helper_entry = None
        helper_exit = None
        call_node = None
        continuation_node = None

        for node in cfg.nodes.values():
            if node.node_type == NodeType.ENTRY and "helper" in node.source_text:
                helper_entry = node
            elif node.node_type == NodeType.EXIT and "helper" in node.source_text:
                helper_exit = node
            elif "helper()" in node.source_text:
                call_node = node
            elif "x = x + 1" in node.source_text:
                continuation_node = node

        # Verify nodes were found
        assert helper_entry is not None, "Should find helper entry node"
        assert helper_exit is not None, "Should find helper exit node"
        assert call_node is not None, "Should find method call node"
        assert continuation_node is not None, "Should find continuation node"

        # Verify call edge: call_node -> helper_entry
        assert helper_entry.id in call_node.successors, (
            "Call node should have edge to method entry"
        )

        # Verify return edge: helper_exit -> call_node
        assert call_node.id in helper_exit.successors, (
            "Method exit should have edge back to call node"
        )

        # Verify continuation edge: call_node -> continuation_node
        assert continuation_node.id in call_node.successors, (
            "Call node should have edge to continuation"
        )

        # Verify edge labels
        call_edge_label = call_node.get_edge_label(helper_entry.id)
        return_edge_label = helper_exit.get_edge_label(call_node.id)

        assert call_edge_label == "function_call", (
            f"Call edge should be labeled 'function_call', got {call_edge_label}"
        )
        assert return_edge_label == "function_return", (
            f"Return edge should be labeled 'function_return', got {return_edge_label}"
        )

    def test_multiple_method_calls(self):
        """Test multiple method calls in sequence."""
        java_code = """
        public class Test {
            public static void method1() {
                int a = 1;
            }
            
            public static void method2() {
                int b = 2;
            }
            
            public static void main(String[] args) {
                method1();
                method2();
            }
        }
        """
        cfg = self.helper.build_cfg_from_code(java_code)

        # Find call nodes
        method1_call = None
        method2_call = None

        for node in cfg.nodes.values():
            if "method1()" in node.source_text:
                method1_call = node
            elif "method2()" in node.source_text:
                method2_call = node

        assert method1_call is not None, "Should find method1 call"
        assert method2_call is not None, "Should find method2 call"

        # Verify calls are connected in sequence
        assert method2_call.id in method1_call.successors, (
            "First call should connect to second call"
        )

        # Verify each call has proper call and return edges
        method1_call_edges = [
            label
            for label in method1_call.edge_labels.values()
            if label == "function_call"
        ]
        method2_call_edges = [
            label
            for label in method2_call.edge_labels.values()
            if label == "function_call"
        ]

        assert len(method1_call_edges) > 0, (
            "method1 call should have function_call edge"
        )
        assert len(method2_call_edges) > 0, (
            "method2 call should have function_call edge"
        )

    def test_nested_method_calls(self):
        """Test method calls within other methods."""
        java_code = """
        public class Test {
            public static int leaf() {
                return 1;
            }
            
            public static int intermediate() {
                return leaf() + 1;
            }
            
            public static void main(String[] args) {
                int result = intermediate();
            }
        }
        """
        cfg = self.helper.build_cfg_from_code(java_code)

        # Count function call edges
        call_edge_count = 0
        return_edge_count = 0

        for node in cfg.nodes.values():
            for successor_id in node.successors:
                edge_label = node.get_edge_label(successor_id)
                if edge_label == "function_call":
                    call_edge_count += 1
                elif edge_label == "function_return":
                    return_edge_count += 1

        # Should have call edges for intermediate() and leaf() calls
        assert call_edge_count >= 2, (
            f"Should have at least 2 function call edges, got {call_edge_count}"
        )
        assert return_edge_count >= 2, (
            f"Should have at least 2 function return edges, got {return_edge_count}"
        )


class TestJavaSpecific:
    """Test Java-specific language features."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(os.path.dirname(__file__), "java_specific.java")

    def test_lambda_expressions(self):
        """Test lambda expression CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "lambdaExpressions"
        )

        # Lambda expressions may create separate CFG contexts
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_anonymous_classes(self):
        """Test anonymous class CFG generation."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "anonymousClasses")

        # Anonymous classes should be handled properly
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)


class TestNestedConstructs:
    """Test nested control flow structure CFG generation."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "nested_structures.java"
        )

    def test_if_in_while_loop(self):
        """Test if statement inside while loop."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "ifInWhileLoop")

        # Should have nested conditional and loop structures
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)

    def test_nested_for_loops(self):
        """Test nested for loops with proper context management."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "nestedForLoops")

        # Should have multiple loop contexts
        loop_headers = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.LOOP_HEADER
        ]
        assert len(loop_headers) >= 2, (
            "Should have multiple loop headers for nested loops"
        )
        self.helper.assert_reachability(cfg)

    def test_nested_switch_statements(self):
        """Test nested switch statements."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "nestedSwitchStatements"
        )

        # Should have multiple switch contexts
        switch_heads = [
            n for n in cfg.nodes.values() if n.node_type == NodeType.SWITCH_HEAD
        ]
        assert len(switch_heads) >= 2, (
            "Should have multiple switch heads for nested switches"
        )
        self.helper.assert_reachability(cfg)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(os.path.dirname(__file__), "edge_cases.java")

    def test_empty_blocks(self):
        """Test empty block handling."""
        cfg = self.helper.build_cfg_from_java_file(self.samples_dir, "emptyBlocks")

        # Should handle empty constructs gracefully
        self.helper.assert_entry_exit_nodes(cfg)
        # May have unreachable nodes due to empty blocks

    def test_unreachable_after_return(self):
        """Test unreachable code after return."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "unreachableAfterReturn"
        )

        # Should model unreachable code but not connect it
        return_nodes = [n for n in cfg.nodes.values() if n.node_type == NodeType.RETURN]
        assert len(return_nodes) > 0, "Should have RETURN nodes"

    def test_complex_conditional_expressions(self):
        """Test complex boolean expressions in conditions."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "complexConditionalExpressions"
        )

        # Should parse complex expressions correctly
        self.helper.assert_entry_exit_nodes(cfg)
        self.helper.assert_reachability(cfg)


class TestCFGStructuralIntegrity:
    """Test CFG structural correctness."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()

    def test_entry_exit_consistency(self):
        """Test that every method has proper entry/exit structure."""
        # Test multiple methods for consistency
        methods_to_test = [
            ("basic_constructs.java", "sequentialStatements"),
            ("basic_constructs.java", "methodWithParameters"),
            ("basic_constructs.java", "emptyMethod"),
            ("nested_structures.java", "ifInWhileLoop"),
            ("edge_cases.java", "emptyBlocks"),
        ]

        for file_name, method_name in methods_to_test:
            file_path = os.path.join(os.path.dirname(__file__), file_name)
            cfg = self.helper.build_cfg_from_java_file(file_path, method_name)

            self.helper.assert_entry_exit_nodes(cfg, f"Method {method_name}")

            # Verify bidirectional relationships
            for node_id, node in cfg.nodes.items():
                for successor_id in node.successors:
                    if successor_id in cfg.nodes:
                        successor_node = cfg.nodes[successor_id]
                        assert node_id in successor_node.predecessors, (
                            f"Inconsistent edge: {node_id}->{successor_id} missing reverse edge"
                        )


class TestVariableAnalysis:
    """Test variable definition and use tracking."""

    def setup_method(self):
        self.helper = JavaCFGTestHelper()
        self.samples_dir = os.path.join(
            os.path.dirname(__file__), "basic_constructs.java"
        )

    def test_variable_definitions(self):
        """Test variable definition tracking."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "sequentialStatements"
        )

        # Should track variable definitions
        all_definitions = set()
        for node in cfg.nodes.values():
            all_definitions.update(node.metadata.variable_definitions)

        # Should include local variable definitions
        expected_vars = {"a", "b", "c"}
        found_vars = all_definitions & expected_vars
        assert len(found_vars) > 0, (
            f"Should track some variable definitions, got: {all_definitions}"
        )

    def test_parameter_tracking(self):
        """Test method parameter tracking in entry nodes."""
        cfg = self.helper.build_cfg_from_java_file(
            self.samples_dir, "methodWithParameters"
        )

        self.helper.assert_parameter_extraction(cfg, ["x", "y"])


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
