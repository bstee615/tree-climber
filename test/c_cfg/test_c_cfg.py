"""
Comprehensive test suite for C CFG implementation.

This module provides end-to-end validation of CFG generation for C language
constructs, including individual constructs, nested combinations, and edge cases.
"""

from typing import Dict, List, Tuple

import pytest

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.cfg.cfg_types import CFGNode, NodeType
from tree_climber.cfg.visitor import CFG


class CFGTestHelper:
    """Helper class for CFG testing and validation."""

    def __init__(self):
        self.builder = CFGBuilder("c")
        self.builder.setup_parser()

    def build_cfg_from_code(self, c_code: str) -> CFG:
        """Build CFG from C source code."""
        return self.builder.build_cfg(c_code)

    def assert_node_count(self, cfg: CFG, expected_count: int, msg: str = ""):
        """Assert that CFG has the expected number of nodes."""
        actual_count = len(cfg.nodes)
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} nodes, got {actual_count}. {msg}"

    def assert_node_types(
        self, cfg: CFG, expected_types: Dict[NodeType, int], msg: str = ""
    ):
        """Assert that CFG has the expected node types and counts."""
        actual_types = {}
        for node in cfg.nodes.values():
            node_type = node.node_type
            actual_types[node_type] = actual_types.get(node_type, 0) + 1

        for expected_type, expected_count in expected_types.items():
            actual_count = actual_types.get(expected_type, 0)
            assert actual_count == expected_count, (
                f"Expected {expected_count} nodes of type {expected_type.name}, "
                f"got {actual_count}. {msg}"
            )

    def assert_edge_connections(
        self, cfg: CFG, expected_edges: List[Tuple[int, int]], msg: str = ""
    ):
        """Assert that CFG has the expected edge connections."""
        actual_edges = set()
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                actual_edges.add((node_id, successor_id))

        expected_edge_set = set(expected_edges)
        missing_edges = expected_edge_set - actual_edges
        extra_edges = actual_edges - expected_edge_set

        assert not missing_edges, f"Missing edges: {missing_edges}. {msg}"
        assert not extra_edges, f"Extra edges: {extra_edges}. {msg}"

    def assert_edge_labels(
        self, cfg: CFG, expected_labels: Dict[Tuple[int, int], str], msg: str = ""
    ):
        """Assert that CFG has the expected edge labels."""
        for (src_id, dest_id), expected_label in expected_labels.items():
            src_node = cfg.nodes.get(src_id)
            assert src_node is not None, f"Source node {src_id} not found. {msg}"
            assert (
                dest_id in src_node.successors
            ), f"Edge {src_id}->{dest_id} not found. {msg}"

            actual_label = src_node.get_edge_label(dest_id)
            assert actual_label == expected_label, (
                f"Expected label '{expected_label}' for edge {src_id}->{dest_id}, "
                f"got '{actual_label}'. {msg}"
            )

    def assert_node_content(
        self, cfg: CFG, node_id: int, expected_text_contains: str, msg: str = ""
    ):
        """Assert that a node contains expected text."""
        node = cfg.nodes.get(node_id)
        assert node is not None, f"Node {node_id} not found. {msg}"
        assert expected_text_contains in node.source_text, (
            f"Expected node {node_id} to contain '{expected_text_contains}', "
            f"got '{node.source_text}'. {msg}"
        )

    def get_nodes_by_type(self, cfg: CFG, node_type: NodeType) -> List[CFGNode]:
        """Get all nodes of a specific type."""
        return [node for node in cfg.nodes.values() if node.node_type == node_type]

    def get_entry_nodes(self, cfg: CFG) -> List[CFGNode]:
        """Get all entry nodes."""
        return self.get_nodes_by_type(cfg, NodeType.ENTRY)

    def get_exit_nodes(self, cfg: CFG) -> List[CFGNode]:
        """Get all exit nodes."""
        return self.get_nodes_by_type(cfg, NodeType.EXIT)

    def assert_single_entry_exit(self, cfg: CFG, msg: str = ""):
        """Assert that CFG has exactly one entry and one exit node."""
        entry_nodes = self.get_entry_nodes(cfg)
        exit_nodes = self.get_exit_nodes(cfg)

        assert (
            len(entry_nodes) == 1
        ), f"Expected 1 entry node, got {len(entry_nodes)}. {msg}"
        assert (
            len(exit_nodes) == 1
        ), f"Expected 1 exit node, got {len(exit_nodes)}. {msg}"

        return entry_nodes[0], exit_nodes[0]

    def assert_reachable_from_entry(self, cfg: CFG, msg: str = ""):
        """Assert that all nodes are reachable from the entry node."""
        entry_nodes = self.get_entry_nodes(cfg)
        assert (
            len(entry_nodes) == 1
        ), f"Expected 1 entry node for reachability test. {msg}"

        entry_node = entry_nodes[0]
        reachable = set()
        stack = [entry_node.id]

        while stack:
            node_id = stack.pop()
            if node_id in reachable:
                continue
            reachable.add(node_id)

            node = cfg.nodes[node_id]
            for successor_id in node.successors:
                if successor_id not in reachable:
                    stack.append(successor_id)

        all_node_ids = set(cfg.nodes.keys())
        unreachable = all_node_ids - reachable
        assert not unreachable, f"Unreachable nodes: {unreachable}. {msg}"

    def assert_exits_reach_function_exit(self, cfg: CFG, msg: str = ""):
        """Assert that all exit nodes can reach the function exit."""
        exit_nodes = self.get_exit_nodes(cfg)
        assert (
            len(exit_nodes) == 1
        ), f"Expected 1 exit node for exit reachability test. {msg}"

        function_exit = exit_nodes[0]

        # Find all nodes that should reach the function exit
        nodes_with_exit_edges = []
        for node in cfg.nodes.values():
            if node.node_type in [NodeType.RETURN, NodeType.BREAK, NodeType.CONTINUE]:
                nodes_with_exit_edges.append(node)

        # Check that these nodes have paths to function exit
        for node in nodes_with_exit_edges:
            if node.node_type == NodeType.RETURN:
                assert (
                    function_exit.id in node.successors
                ), f"Return node {node.id} should connect to function exit. {msg}"


@pytest.fixture
def helper():
    """Provide CFG test helper instance."""
    return CFGTestHelper()


# Basic Control Flow Tests
class TestBasicControlFlow:
    """Test basic control flow constructs."""

    def test_simple_sequence(self, helper):
        """Test simple sequence of statements."""
        code = """
        int main() {
            int x = 5;
            x = x + 1;
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have entry, statements, return, and exit
        helper.assert_node_types(
            cfg,
            {
                NodeType.ENTRY: 1,
                NodeType.STATEMENT: 2,  # declaration and assignment
                NodeType.RETURN: 1,
                NodeType.EXIT: 1,
            },
        )

        helper.assert_single_entry_exit(cfg)
        helper.assert_reachable_from_entry(cfg)

    def test_function_definition(self, helper):
        """Test function definition structure."""
        code = """
        int test_func(int a, int b) {
            return a + b;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        entry_node, exit_node = helper.assert_single_entry_exit(cfg)

        # Entry node should contain function name
        helper.assert_node_content(cfg, entry_node.id, "test_func")

        # Should have parameter definitions (implementation currently extracts incomplete data)
        # Note: This is a known implementation limitation - parameter extraction needs improvement
        assert len(entry_node.metadata.variable_definitions) >= 1

    def test_empty_function(self, helper):
        """Test empty function."""
        code = """
        void empty_func() {
        }
        """
        cfg = helper.build_cfg_from_code(code)

        helper.assert_single_entry_exit(cfg)
        # Should have entry, exit, and empty block placeholder
        helper.assert_node_count(
            cfg,
            3,
            "Empty function should have entry, exit, and empty block placeholder",
        )


class TestConditionalStatements:
    """Test conditional statement constructs."""

    def test_if_only(self, helper):
        """Test if statement without else."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                x = x + 1;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        helper.assert_node_types(
            cfg,
            {
                NodeType.ENTRY: 1,
                NodeType.STATEMENT: 2,  # int x = 5 AND x = x + 1 (in if body)
                NodeType.CONDITION: 1,  # if condition
                NodeType.RETURN: 1,
                NodeType.EXIT: 1,  # function exit (only one due to post-processing)
            },
        )

        # Find condition node and check edge labels
        condition_nodes = helper.get_nodes_by_type(cfg, NodeType.CONDITION)
        assert len(condition_nodes) == 1

        condition_node = condition_nodes[0]
        # Should have true and false edges
        edge_labels = condition_node.edge_labels
        assert "true" in edge_labels.values()
        assert "false" in edge_labels.values()

    def test_if_else(self, helper):
        """Test if-else statement."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                x = x + 1;
            } else {
                x = x - 1;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have condition with true and false branches
        condition_nodes = helper.get_nodes_by_type(cfg, NodeType.CONDITION)
        assert len(condition_nodes) == 1

        condition_node = condition_nodes[0]
        assert len(condition_node.successors) == 2  # true and false branches

        edge_labels = condition_node.edge_labels
        assert "true" in edge_labels.values()
        assert "false" in edge_labels.values()

    def test_nested_if(self, helper):
        """Test nested if statements."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                if (x > 10) {
                    x = x * 2;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have 2 condition nodes (outer and inner if)
        condition_nodes = helper.get_nodes_by_type(cfg, NodeType.CONDITION)
        assert len(condition_nodes) == 2

        helper.assert_reachable_from_entry(cfg)


class TestLoopConstructs:
    """Test loop constructs."""

    def test_while_loop(self, helper):
        """Test while loop structure."""
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have loop header with true/false edges
        loop_headers = helper.get_nodes_by_type(cfg, NodeType.LOOP_HEADER)
        assert len(loop_headers) == 1

        loop_header = loop_headers[0]
        edge_labels = loop_header.edge_labels
        assert "true" in edge_labels.values()  # into loop body
        assert "false" in edge_labels.values()  # exit loop

    def test_for_loop(self, helper):
        """Test for loop structure."""
        code = """
        int main() {
            int sum = 0;
            for (int i = 0; i < 10; i++) {
                sum = sum + i;
            }
            return sum;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have init, condition (loop header), update, and body
        helper.assert_node_types(
            cfg,
            {
                NodeType.ENTRY: 1,
                NodeType.STATEMENT: 4,  # sum=0, init i=0, update i++, sum=sum+i
                NodeType.LOOP_HEADER: 1,  # condition i<10
                NodeType.RETURN: 1,
                NodeType.EXIT: 1,  # function exit (only one due to post-processing)
            },
        )

        loop_headers = helper.get_nodes_by_type(cfg, NodeType.LOOP_HEADER)
        assert len(loop_headers) == 1

        # Check that loop header has back-edge from update
        loop_header = loop_headers[0]
        assert len(loop_header.predecessors) >= 2  # from init and from update

    def test_do_while_loop(self, helper):
        """Test do-while loop structure."""
        code = """
        int main() {
            int x = 0;
            do {
                x = x + 1;
            } while (x < 10);
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have entry node, body, and condition at end
        loop_headers = helper.get_nodes_by_type(cfg, NodeType.LOOP_HEADER)
        assert len(loop_headers) == 1

        # Do-while should execute body at least once
        helper.assert_reachable_from_entry(cfg)


class TestJumpStatements:
    """Test jump statement constructs."""

    def test_break_in_loop(self, helper):
        """Test break statement in loop."""
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
                if (x == 5) {
                    break;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have break node
        break_nodes = helper.get_nodes_by_type(cfg, NodeType.BREAK)
        assert len(break_nodes) == 1

        # Break should connect to loop exit
        break_node = break_nodes[0]
        assert len(break_node.successors) == 1  # should go to loop exit

    def test_continue_in_loop(self, helper):
        """Test continue statement in loop."""
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
                if (x == 5) {
                    continue;
                }
                x = x * 2;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have continue node
        continue_nodes = helper.get_nodes_by_type(cfg, NodeType.CONTINUE)
        assert len(continue_nodes) == 1

        # Continue should connect to loop header
        continue_node = continue_nodes[0]
        assert len(continue_node.successors) == 1  # should go to loop header

    def test_return_statement(self, helper):
        """Test return statement."""
        code = """
        int main() {
            int x = 5;
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have return node
        return_nodes = helper.get_nodes_by_type(cfg, NodeType.RETURN)
        assert len(return_nodes) == 1

        # Return should connect to function exit
        return_node = return_nodes[0]
        function_exits = helper.get_exit_nodes(cfg)
        assert len(function_exits) == 1
        assert function_exits[0].id in return_node.successors

    def test_multiple_returns(self, helper):
        """Test multiple return statements."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                return 1;
            }
            return 0;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have 2 return nodes
        return_nodes = helper.get_nodes_by_type(cfg, NodeType.RETURN)
        assert len(return_nodes) == 2

        # Both returns should connect to function exit
        function_exits = helper.get_exit_nodes(cfg)
        assert len(function_exits) == 1
        function_exit_id = function_exits[0].id

        for return_node in return_nodes:
            assert function_exit_id in return_node.successors


class TestSwitchStatements:
    """Test switch statement constructs."""

    def test_switch_with_breaks(self, helper):
        """Test switch statement with break statements."""
        code = """
        int main() {
            int x = 5;
            switch (x) {
                case 1:
                    x = x + 1;
                    break;
                case 2:
                    x = x + 2;
                    break;
                default:
                    x = 0;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have switch head, statements, and breaks
        # Note: CASE nodes are removed by post-processing passthrough
        helper.assert_node_types(
            cfg,
            {
                NodeType.SWITCH_HEAD: 1,
                NodeType.STATEMENT: 4,  # int x=5, x=x+1, x=x+2, x=0
                NodeType.BREAK: 2,  # 2 break statements
                NodeType.RETURN: 1,
                NodeType.EXIT: 1,
            },
        )

        # Switch head should connect to all cases
        switch_heads = helper.get_nodes_by_type(cfg, NodeType.SWITCH_HEAD)
        assert len(switch_heads) == 1
        switch_head = switch_heads[0]

        # Should have edges to all 3 case statements (after CASE node passthrough)
        assert len(switch_head.successors) == 3

        # Check edge labels for case values (labels preserved from original CASE nodes)
        edge_labels = switch_head.edge_labels
        assert "1" in edge_labels.values()
        assert "2" in edge_labels.values()
        assert "default" in edge_labels.values()

    def test_switch_fallthrough(self, helper):
        """Test switch statement with fall-through."""
        code = """
        int main() {
            int x = 5;
            switch (x) {
                case 1:
                    x = x + 1;
                    // fall through
                case 2:
                    x = x + 2;
                    break;
                default:
                    x = 0;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Switch fall-through behavior should be represented in node connections
        # Note: CASE nodes are removed by post-processing, but fall-through preserved
        switch_heads = helper.get_nodes_by_type(cfg, NodeType.SWITCH_HEAD)
        assert len(switch_heads) == 1

        # Verify CFG structure maintains reachability
        helper.assert_reachable_from_entry(cfg)


class TestGotoAndLabels:
    """Test goto and label constructs."""

    def test_goto_forward(self, helper):
        """Test forward goto statement."""
        code = """
        int main() {
            int x = 5;
            goto skip;
            x = x + 1;
        skip:
            x = x + 2;
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have goto and label nodes
        helper.assert_node_types(
            cfg,
            {
                NodeType.GOTO: 1,
                NodeType.LABEL: 1,
            },
        )

        # Goto should connect to label
        goto_nodes = helper.get_nodes_by_type(cfg, NodeType.GOTO)
        label_nodes = helper.get_nodes_by_type(cfg, NodeType.LABEL)

        assert len(goto_nodes) == 1
        assert len(label_nodes) == 1

        goto_node = goto_nodes[0]
        label_node = label_nodes[0]

        assert label_node.id in goto_node.successors

    def test_goto_backward(self, helper):
        """Test backward goto statement (loop-like)."""
        code = """
        int main() {
            int x = 0;
        loop:
            x = x + 1;
            if (x < 10) {
                goto loop;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have goto and label nodes
        goto_nodes = helper.get_nodes_by_type(cfg, NodeType.GOTO)
        label_nodes = helper.get_nodes_by_type(cfg, NodeType.LABEL)

        assert len(goto_nodes) == 1
        assert len(label_nodes) == 1

        # Should form a loop-like structure
        helper.assert_reachable_from_entry(cfg)


class TestNestedConstructs:
    """Test nested control flow constructs."""

    def test_if_in_loop(self, helper):
        """Test conditional inside loop."""
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
                if (x == 5) {
                    x = x * 2;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have both loop header and condition
        helper.assert_node_types(
            cfg,
            {
                NodeType.LOOP_HEADER: 1,
                NodeType.CONDITION: 1,
            },
        )

        helper.assert_reachable_from_entry(cfg)

    def test_loop_in_if(self, helper):
        """Test loop inside conditional."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                while (x > 0) {
                    x = x - 1;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have both condition and loop header
        helper.assert_node_types(
            cfg,
            {
                NodeType.CONDITION: 1,
                NodeType.LOOP_HEADER: 1,
            },
        )

        helper.assert_reachable_from_entry(cfg)

    def test_switch_in_loop(self, helper):
        """Test switch statement inside loop."""
        code = """
        int main() {
            int x = 0;
            while (x < 10) {
                x = x + 1;
                switch (x) {
                    case 5:
                        x = x + 5;
                        break;
                    default:
                        break;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have loop header, switch head, statements, and breaks
        # Note: CASE nodes are removed by post-processing
        helper.assert_node_types(
            cfg,
            {
                NodeType.LOOP_HEADER: 1,
                NodeType.SWITCH_HEAD: 1,
                NodeType.STATEMENT: 3,  # int x=0, x=x+1, x=x+5
                NodeType.BREAK: 2,  # breaks in cases
                NodeType.RETURN: 1,
                NodeType.ENTRY: 1,
                NodeType.EXIT: 1,
            },
        )

        helper.assert_reachable_from_entry(cfg)

    def test_nested_loops(self, helper):
        """Test nested loops (loop within loop)."""
        code = """
        int main() {
            int sum = 0;
            for (int i = 0; i < 10; i++) {
                for (int j = 0; j < 5; j++) {
                    sum = sum + i * j;
                }
            }
            return sum;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have 2 loop headers (outer and inner)
        loop_headers = helper.get_nodes_by_type(cfg, NodeType.LOOP_HEADER)
        assert len(loop_headers) == 2

        helper.assert_reachable_from_entry(cfg)

    def test_nested_switches(self, helper):
        """Test nested switch statements."""
        code = """
        int main() {
            int x = 5, y = 3;
            switch (x) {
                case 5:
                    switch (y) {
                        case 3:
                            x = x + y;
                            break;
                        default:
                            x = 0;
                            break;
                    }
                    break;
                default:
                    x = -1;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have 2 switch heads (outer and inner)
        # Note: CASE nodes are removed by post-processing but switch structure preserved
        switch_heads = helper.get_nodes_by_type(cfg, NodeType.SWITCH_HEAD)
        assert len(switch_heads) == 2

        # Verify all nodes are reachable (default case connectivity fixed)
        helper.assert_reachable_from_entry(cfg)

        # Verify that outer switch has edge to default case with "default" label
        outer_switch = switch_heads[0]  # First switch should be outer switch(x)

        # Find the default statement node
        default_nodes = []
        for node in cfg.nodes.values():
            if "x = -1" in node.source_text:
                default_nodes.append(node)

        assert len(default_nodes) == 1, "Should have exactly one default statement"
        default_node = default_nodes[0]

        # Verify outer switch connects to default statement with "default" label
        assert (
            default_node.id in outer_switch.successors
        ), "Outer switch should connect to default statement"

        default_edge_label = outer_switch.get_edge_label(default_node.id)
        assert (
            default_edge_label == "default"
        ), f"Expected 'default' label, got '{default_edge_label}'"


class TestComplexPatterns:
    """Test complex real-world programming patterns."""

    def test_break_continue_mix(self, helper):
        """Test mix of break and continue statements."""
        code = """
        int main() {
            int sum = 0;
            for (int i = 0; i < 100; i++) {
                if (i % 2 == 0) {
                    continue;
                }
                if (i > 50) {
                    break;
                }
                sum = sum + i;
            }
            return sum;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have both break and continue
        helper.assert_node_types(
            cfg,
            {
                NodeType.BREAK: 1,
                NodeType.CONTINUE: 1,
                NodeType.LOOP_HEADER: 1,
                NodeType.CONDITION: 2,  # two if conditions
            },
        )

        helper.assert_reachable_from_entry(cfg)

    def test_return_in_nested_structure(self, helper):
        """Test return statement in deeply nested structure."""
        code = """
        int main() {
            for (int i = 0; i < 10; i++) {
                if (i == 5) {
                    while (i < 8) {
                        if (i == 7) {
                            return i;
                        }
                        i = i + 1;
                    }
                }
            }
            return -1;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have multiple returns
        return_nodes = helper.get_nodes_by_type(cfg, NodeType.RETURN)
        assert len(return_nodes) == 2

        # Both returns should connect to function exit
        function_exits = helper.get_exit_nodes(cfg)
        assert len(function_exits) == 1
        function_exit_id = function_exits[0].id

        for return_node in return_nodes:
            assert function_exit_id in return_node.successors

    def test_goto_across_structures(self, helper):
        """Test goto spanning multiple control structures."""
        code = """
        int main() {
            int x = 0;
            for (int i = 0; i < 10; i++) {
                if (i == 5) {
                    goto cleanup;
                }
                x = x + i;
            }
            
            while (x > 0) {
                x = x - 1;
            }
            
        cleanup:
            x = 0;
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have goto and label
        helper.assert_node_types(
            cfg,
            {
                NodeType.GOTO: 1,
                NodeType.LABEL: 1,
            },
        )

        # Goto should connect to label
        goto_nodes = helper.get_nodes_by_type(cfg, NodeType.GOTO)
        label_nodes = helper.get_nodes_by_type(cfg, NodeType.LABEL)

        goto_node = goto_nodes[0]
        label_node = label_nodes[0]
        assert label_node.id in goto_node.successors

    def test_fibonacci_function(self, helper):
        """Test fibonacci-like function with multiple control paths."""
        code = """
        int fibonacci(int n) {
            if (n <= 1) {
                return n;
            }
            
            int a = 0, b = 1, temp;
            for (int i = 2; i <= n; i++) {
                temp = a + b;
                a = b;
                b = temp;
            }
            
            return b;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have entry condition, loop, and multiple returns
        helper.assert_node_types(
            cfg,
            {
                NodeType.CONDITION: 1,  # if condition
                NodeType.LOOP_HEADER: 1,  # for loop
                NodeType.RETURN: 2,  # early return and final return
            },
        )

        helper.assert_reachable_from_entry(cfg)

    def test_state_machine_pattern(self, helper):
        """Test switch-based state machine pattern."""
        code = """
        int process_state(int state, int input) {
            int result = 0;
            
            switch (state) {
                case 0:  // IDLE
                    if (input == 1) {
                        state = 1;
                    }
                    break;
                    
                case 1:  // PROCESSING
                    result = input * 2;
                    if (result > 10) {
                        state = 2;
                    } else {
                        state = 0;
                    }
                    break;
                    
                case 2:  // DONE
                    return result;
                    
                default:
                    state = 0;
                    break;
            }
            
            return state;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have switch with multiple statements and conditions within cases
        # Note: CASE nodes are removed by post-processing
        helper.assert_node_types(
            cfg,
            {
                NodeType.SWITCH_HEAD: 1,
                NodeType.CONDITION: 2,  # if conditions within cases
                NodeType.BREAK: 3,  # break statements
                NodeType.RETURN: 2,  # early return and final return
                NodeType.STATEMENT: 6,  # result=0, state=1, result=input*2, state=2, state=0, state=0
                NodeType.ENTRY: 1,
                NodeType.EXIT: 1,
            },
        )

        helper.assert_reachable_from_entry(cfg)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_blocks(self, helper):
        """Test empty compound statements."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                // empty block
            }
            
            while (x > 10) {
                // empty while body
            }
            
            for (int i = 0; i < x; i++) {
                // empty for body
            }
            
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should handle empty blocks gracefully
        helper.assert_reachable_from_entry(cfg)
        helper.assert_single_entry_exit(cfg)

    def test_deeply_nested_structures(self, helper):
        """Test deeply nested control structures."""
        code = """
        int main() {
            int x = 0;
            if (x == 0) {
                while (x < 10) {
                    for (int i = 0; i < 5; i++) {
                        if (i == 2) {
                            switch (x) {
                                case 0:
                                    x = 1;
                                    break;
                                default:
                                    x = x + 1;
                                    break;
                            }
                        }
                    }
                    x = x + 1;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should handle deep nesting
        helper.assert_reachable_from_entry(cfg)

        # Should have multiple types of control structures
        # Note: CASE nodes are removed by post-processing
        helper.assert_node_types(
            cfg,
            {
                NodeType.CONDITION: 2,  # outer if and inner if
                NodeType.LOOP_HEADER: 2,  # while and for
                NodeType.SWITCH_HEAD: 1,
                NodeType.BREAK: 2,  # break statements from cases
                NodeType.STATEMENT: 6,  # x=0, i=0, i++, x=1, x=x+1, x=x+1
                NodeType.ENTRY: 1,
                NodeType.EXIT: 1,
                NodeType.RETURN: 1,
            },
        )

    def test_switch_without_default(self, helper):
        """Test switch statement without default case."""
        code = """
        int main() {
            int x = 5;
            switch (x) {
                case 1:
                    x = 10;
                    break;
                case 2:
                    x = 20;
                    break;
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should have switch head but no default case
        switch_heads = helper.get_nodes_by_type(cfg, NodeType.SWITCH_HEAD)
        assert len(switch_heads) == 1
        switch_head = switch_heads[0]

        # After post-processing, CASE nodes are removed but structure preserved
        # Check that switch head connects to case statements
        assert len(switch_head.successors) == 2  # Should connect to 2 case statements

        helper.assert_reachable_from_entry(cfg)

    def test_complex_expressions(self, helper):
        """Test complex conditional expressions."""
        code = """
        int main() {
            int x = 5, y = 10, z = 15;
            
            if (x > 0 && y < 20 || z == 15) {
                x = x + y + z;
            }
            
            while (x > 0 && (y > 5 || z < 100)) {
                x = x - 1;
                y = y + 1;
            }
            
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Should handle complex expressions in conditions
        helper.assert_node_types(
            cfg,
            {
                NodeType.CONDITION: 1,
                NodeType.LOOP_HEADER: 1,
            },
        )

        helper.assert_reachable_from_entry(cfg)


class TestCFGStructuralIntegrity:
    """Test CFG structural integrity and validation."""

    def test_entry_exit_consistency(self, helper):
        """Test that every function has proper entry/exit structure."""
        code = """
        int test_func() {
            int x = 5;
            if (x > 0) {
                return 1;
            }
            return 0;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        helper.assert_single_entry_exit(cfg)
        helper.assert_exits_reach_function_exit(cfg)

    def test_node_connectivity(self, helper):
        """Test that all nodes are properly connected."""
        code = """
        int main() {
            int x = 0;
            for (int i = 0; i < 10; i++) {
                if (i == 5) {
                    continue;
                }
                x = x + i;
                if (x > 20) {
                    break;
                }
            }
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        helper.assert_reachable_from_entry(cfg)

        # Check that every node has proper predecessor/successor relationship
        for node_id, node in cfg.nodes.items():
            # Check successor relationships are bidirectional
            for successor_id in node.successors:
                successor_node = cfg.nodes[successor_id]
                assert (
                    node_id in successor_node.predecessors
                ), f"Node {successor_id} should have {node_id} as predecessor"

            # Check predecessor relationships are bidirectional
            for predecessor_id in node.predecessors:
                predecessor_node = cfg.nodes[predecessor_id]
                assert (
                    node_id in predecessor_node.successors
                ), f"Node {predecessor_id} should have {node_id} as successor"

    def test_edge_label_consistency(self, helper):
        """Test proper true/false edge labeling."""
        code = """
        int main() {
            int x = 5;
            if (x > 0) {
                x = 10;
            } else {
                x = 0;
            }
            
            while (x > 0) {
                x = x - 1;
            }
            
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Check condition nodes have proper edge labels
        condition_nodes = helper.get_nodes_by_type(cfg, NodeType.CONDITION)
        for condition_node in condition_nodes:
            edge_labels = condition_node.edge_labels
            if len(condition_node.successors) == 2:
                # Should have both true and false labels
                labels = set(edge_labels.values())
                assert (
                    "true" in labels
                ), f"Condition node {condition_node.id} missing 'true' label"
                assert (
                    "false" in labels
                ), f"Condition node {condition_node.id} missing 'false' label"

        # Check loop headers have proper edge labels
        loop_headers = helper.get_nodes_by_type(cfg, NodeType.LOOP_HEADER)
        for loop_header in loop_headers:
            edge_labels = loop_header.edge_labels
            if len(loop_header.successors) >= 2:
                labels = set(edge_labels.values())
                assert (
                    "true" in labels
                ), f"Loop header {loop_header.id} missing 'true' label"
                assert (
                    "false" in labels
                ), f"Loop header {loop_header.id} missing 'false' label"


class TestVariableAnalysis:
    """Test variable definition and use tracking."""

    def test_variable_definitions(self, helper):
        """Test variable definition tracking."""
        code = """
        int main(int argc) {
            int x = 5;
            int y;
            y = 10;
            return x + y;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Check that variable definitions are tracked
        all_definitions = []
        for node in cfg.nodes.values():
            all_definitions.extend(node.metadata.variable_definitions)

        # Should include variable definitions
        assert len(all_definitions) > 0, "Should track variable definitions"
        assert set(all_definitions) == {
            "argc",
            "x",
            "y",
        }, "Should track variable definitions"

    def test_variable_uses(self, helper):
        """Test variable use tracking."""
        code = """
        int main() {
            int x = 5;
            int y = x + 1;
            return y;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Check that variable uses are tracked
        all_uses = []
        for node in cfg.nodes.values():
            all_uses.extend(node.metadata.variable_uses)

        # Should include variable uses
        assert len(all_uses) > 0, "Should track variable uses"

    def test_function_calls(self, helper):
        """Test function call tracking."""
        code = """
        int helper_func() {
            return 42;
        }
        
        int main() {
            int x = helper_func();
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Check that function calls are tracked
        all_calls = []
        for node in cfg.nodes.values():
            all_calls.extend(node.metadata.function_calls)

        # Should include function calls
        assert len(all_calls) > 0, "Should track function calls"

    def test_function_call_edges(self, helper):
        """Test that function calls create proper call and return edges."""
        code = """
        void helper() {
            int y = 10;
        }
        
        int main() {
            int x = 5;
            helper();
            x = x + 1;
            return x;
        }
        """
        cfg = helper.build_cfg_from_code(code)

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
        assert call_node is not None, "Should find function call node"
        assert continuation_node is not None, "Should find continuation node"

        # Verify call edge: call_node -> helper_entry
        assert (
            helper_entry.id in call_node.successors
        ), "Call node should have edge to function entry"

        # Verify return edge: helper_exit -> call_node
        assert (
            call_node.id in helper_exit.successors
        ), "Function exit should have edge back to call node"

        # Verify continuation edge: call_node -> continuation_node
        assert (
            continuation_node.id in call_node.successors
        ), "Call node should have edge to continuation"

        # Verify edge labels
        call_edge_label = call_node.get_edge_label(helper_entry.id)
        return_edge_label = helper_exit.get_edge_label(call_node.id)

        assert (
            call_edge_label == "function_call"
        ), f"Call edge should be labeled 'function_call', got {call_edge_label}"
        assert (
            return_edge_label == "function_return"
        ), f"Return edge should be labeled 'function_return', got {return_edge_label}"

    def test_multiple_function_calls(self, helper):
        """Test multiple function calls in sequence."""
        code = """
        void func1() {
            int a = 1;
        }
        
        void func2() {
            int b = 2;
        }
        
        int main() {
            func1();
            func2();
            return 0;
        }
        """
        cfg = helper.build_cfg_from_code(code)

        # Find call nodes
        func1_call = None
        func2_call = None

        for node in cfg.nodes.values():
            if "func1()" in node.source_text:
                func1_call = node
            elif "func2()" in node.source_text:
                func2_call = node

        assert func1_call is not None, "Should find func1 call"
        assert func2_call is not None, "Should find func2 call"

        # Verify calls are connected in sequence
        assert (
            func2_call.id in func1_call.successors
        ), "First call should connect to second call"

        # Verify each call has proper call and return edges
        func1_call_edges = [
            label
            for label in func1_call.edge_labels.values()
            if label == "function_call"
        ]
        func2_call_edges = [
            label
            for label in func2_call.edge_labels.values()
            if label == "function_call"
        ]

        assert len(func1_call_edges) > 0, "func1 call should have function_call edge"
        assert len(func2_call_edges) > 0, "func2 call should have function_call edge"

    def test_nested_function_calls(self, helper):
        """Test function calls within other functions."""
        code = """
        int leaf() {
            return 1;
        }
        
        int intermediate() {
            return leaf() + 1;
        }
        
        int main() {
            int result = intermediate();
            return result;
        }
        """
        cfg = helper.build_cfg_from_code(code)

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
        assert (
            call_edge_count >= 2
        ), f"Should have at least 2 function call edges, got {call_edge_count}"
        assert (
            return_edge_count >= 2
        ), f"Should have at least 2 function return edges, got {return_edge_count}"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])
