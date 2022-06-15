from tree_sitter_cfg.base_visitor import BaseVisitor
import networkx as nx

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
    
    def add_cfg_node(self, ast_node, label):
        node_id = self.node_id
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
        node_id = self.add_cfg_node(n, f"{n.type}\n`{n.text.decode()}`")
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
        assert condition.type in ("binary_expression",), condition.type
        condition_id = self.add_cfg_node(condition, f"{condition.type}\n`{condition.text.decode()}`")
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append(condition_id)

        compound_statement = n.children[2]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"

        if len(n.children) > 3:
            else_compound_statement = n.children[4]
            assert else_compound_statement.type == "compound_statement", else_compound_statement.type
            old_fringe = self.fringe
            self.fringe = [condition_id]
            self.visit(else_compound_statement)
            self.fringe = old_fringe + self.fringe
        else:
            self.fringe.append(condition_id)

    def visit_for_statement(self, n, **kwargs):
        init = n.children[2]
        cond = n.children[3]
        incr = n.children[5]
        
        assert init.type in ("declaration",), cond.type
        assert cond.type in ("binary_expression",), cond.type
        assert incr.type in ("update_expression",), cond.type

        init_id = self.add_cfg_node(init, f"{init.type}\n`{init.text.decode()}`")
        cond_id = self.add_cfg_node(cond, f"{cond.type}\n`{cond.text.decode()}`")
        incr_id = self.add_cfg_node(incr, f"{incr.type}\n`{incr.text.decode()}`")

        self.add_edge_from_fringe_to(init_id)
        self.cfg.add_edge(init_id, cond_id)
        self.fringe.append(cond_id)

        compound_statement = n.children[7]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(incr_id)
        self.cfg.add_edge(incr_id, cond_id)
        self.fringe.append(cond_id)

    def visit_while_statement(self, n, **kwargs):
        cond = n.children[1].children[1]
        
        assert cond.type in ("binary_expression",), cond.type

        cond_id = self.add_cfg_node(cond, f"{cond.type}\n`{cond.text.decode()}`")

        self.cfg.add_edges_from(zip(self.fringe, [cond_id] * len(self.fringe)))
        self.fringe = []
        self.fringe.append(cond_id)

        compound_statement = n.children[2]
        assert compound_statement.type == "compound_statement", compound_statement.type
        self.visit(compound_statement)
        assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)
