from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx

boolean_expressions = {"binary_expression", "true"}
branch_targets = {"compound_statement", "expression_statement"}

class CFGCreator(BaseVisitor):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self):
        super(CFGCreator).__init__()
        self.cfg = nx.DiGraph()
        self.node_id = 0
        self.fringe = []
    
    def add_cfg_node(self, ast_node, label=None):
        node_id = self.node_id
        if label is None:
            label = f"{ast_node.type} ({ast_node.start_point}, {ast_node.end_point})\n`{ast_node.text.decode()}`"
        self.cfg.add_node(node_id, n=ast_node, label=label)
        self.node_id += 1
        return node_id
    
    def add_edge_from_fringe_to(self, node_id):
        # TODO: assign edge type
        self.cfg.add_edges_from(zip(self.fringe, [node_id] * len(self.fringe)))
        self.fringe = []
    
    """
    VISITOR RULES
    """

    def visit_function_definition(self, n, **kwargs):
        entry_id = self.add_cfg_node(n, "FUNC_ENTRY")
        self.fringe.append(entry_id)
        self.visit_children(n, **kwargs)
        exit_id = self.add_cfg_node(n, "FUNC_EXIT")
        self.add_edge_from_fringe_to(exit_id)

    def visit_default(self, n, indentation_level, **kwargs):
        self.visit_children(n, indentation_level)

    """STRAIGHT LINE STATEMENTS"""

    def enter_statement(self, n):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.fringe.append(node_id)

    def visit_expression_statement(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    def visit_init_declarator(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    """STRUCTURED CONTROL FLOW"""

    def visit_if_statement(self, n, **kwargs):
        condition = n.children[1].children[1]
        assert condition.type in boolean_expressions, condition.type
        condition_id = self.add_cfg_node(condition)
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append(condition_id)

        compound_statement = n.children[2]
        assert compound_statement.type in branch_targets, compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"

        if len(n.children) > 3:
            else_compound_statement = n.children[4]
            assert else_compound_statement.type in branch_targets, else_compound_statement.type
            old_fringe = self.fringe
            self.fringe = [condition_id]
            self.visit(else_compound_statement)
            self.fringe = old_fringe + self.fringe
        else:
            self.fringe.append(condition_id)

    def visit_for_statement(self, n, **kwargs):
        initial_offset = 2
        init = n.children[initial_offset]
        if init.type == ";":
            init = None
        else:
            assert init.type in ("declaration",), init.type
        initial_offset += 1
        cond = n.children[initial_offset]
        if cond.type == ";":
            cond = None
            initial_offset += 1
        else:
            initial_offset += 2
            assert cond.type in boolean_expressions, cond.type
        incr = n.children[initial_offset]
        if incr.type == ")":
            initial_offset += 1
            incr = None
        else:
            initial_offset += 2
            assert incr.type in ("update_expression",), incr.type

        if cond is not None:
            cond_id = self.add_cfg_node(cond)
        else:
            cond_id = self.add_cfg_node(None, f"<TRUE>")

        if init is not None:
            init_id = self.add_cfg_node(init)
            self.add_edge_from_fringe_to(init_id)
            self.cfg.add_edge(init_id, cond_id)
        else:
            self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

        compound_statement = n.children[initial_offset]
        assert compound_statement.type in branch_targets, compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        if incr is not None:
            incr_id = self.add_cfg_node(incr)
            self.add_edge_from_fringe_to(incr_id)
            self.cfg.add_edge(incr_id, cond_id)
        else:
            self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

    def visit_while_statement(self, n, **kwargs):
        cond = n.children[1].children[1]
        
        assert cond.type in boolean_expressions, cond.type

        cond_id = self.add_cfg_node(cond)

        self.cfg.add_edges_from(zip(self.fringe, [cond_id] * len(self.fringe)))
        self.fringe = []
        self.fringe.append(cond_id)

        compound_statement = n.children[2]
        assert compound_statement.type in branch_targets, compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

def test_if_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true) {
            x += 5;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_nocompound():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true)
            x += 5;
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_empty():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true) {
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (3, 2)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_noelse():
    tree = c_parser.parse(bytes("""int main()
    {
        if (x > 1) {
            x += 5;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_else():
    tree = c_parser.parse(bytes("""int main()
    {
        if (x > 1) {
            x += 5;
        }
        else {
            x += 50;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_for_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10; i ++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10; i ++)
            x = 0;
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinit():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; i < 10; i ++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nocond():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; ; i++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10;) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinitincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; i < 10;) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinitcond():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; ; i++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nocondincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; ; ) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nothing():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; ; ) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(v.cfg))) == 1
