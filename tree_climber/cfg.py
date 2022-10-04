from collections import defaultdict
import warnings
from matplotlib import pyplot as plt
import networkx as nx
from tree_climber.tree_sitter_utils import c_parser
from tree_climber.ast import make_ast


class CFGVisitor:
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self, ast):
        super(CFGVisitor).__init__()
        self.ast = ast
        self.cfg = nx.MultiDiGraph()
        self.node_id = 0
        self.returns = []
        self.fringe = []
        self.break_fringe = []
        self.continue_fringe = []
        self.gotos = {}
        self.labels = {}

    """
    TRAVERSAL UTILITIES
    """

    def get_attr(self, n, attrname):
        return self.ast.nodes[n][attrname]

    def get_type(self, n):
        return self.get_attr(n, "type")

    def get_text(self, n):
        return self.get_attr(n, "text")

    def get_children(self, n):
        return list(self.ast.successors(n))

    def get_named_children(self, n):
        is_named = nx.get_node_attributes(self.ast, "is_named")
        return [c for c in self.ast.successors(n) if is_named[c]]

    """
    CFG ASSEMBLY UTILITIES
    """

    def add_dummy_node(self):
        """dummy nodes are nodes whose connections should be forwarded in a post-processing step"""
        node_id = self.node_id
        self.cfg.add_node(node_id, dummy=True, label="DUMMY")
        self.node_id += 1
        return node_id

    def add_cfg_node(self, ast_node, label=None, **kwargs):
        node_id = self.node_id
        ast_kwargs = {}
        if ast_node is not None:
            attr = self.ast.nodes[ast_node]
            ast_kwargs.update(attr)
        if label is not None:
            ast_kwargs["label"] = label
        if ast_node is None:
            ast_kwargs["color"] = "green"
        else:
            ast_kwargs["ast_node"] = ast_node
        ast_kwargs.update(kwargs)
        self.cfg.add_node(node_id, **ast_kwargs)
        self.node_id += 1
        return node_id

    def add_edge_from_fringe_to(self, node_id):
        # Assign edges with labels
        fringe_by_type = defaultdict(list)
        for source in self.fringe:
            if isinstance(source, tuple):
                fringe_by_type[source[1]].append(source[0])
            else:
                fringe_by_type[None].append(source)
        for edge_type, fringe in fringe_by_type.items():
            kwargs = {}
            if edge_type is not None:
                kwargs["label"] = str(edge_type)
            self.cfg.add_edges_from(zip(fringe, [node_id] * len(self.fringe)), **kwargs)
        self.fringe = []

    """
    VISITOR RULES
    """

    def visit(self, n, **kwargs):
        return getattr(
            self, "visit_" + self.get_type(n), self.visit_default
        )(n=n, **kwargs)

    def visit_children(self, n, **kwargs):
        for c in self.get_children(n):
            should_continue = self.visit(c, **kwargs)
            if should_continue == False:
                break

    def visit_function_definition(self, n, **kwargs):
        entry_id = self.add_cfg_node(None, "FUNC_ENTRY")
        self.cfg.graph["entry"] = entry_id
        self.add_edge_from_fringe_to(entry_id)
        self.fringe.append(entry_id)
        self.visit_children(n, **kwargs)
        exit_id = self.add_cfg_node(None, "FUNC_EXIT")
        self.add_edge_from_fringe_to(exit_id)
        # paste goto edges
        for label in self.gotos:
            try:
                self.cfg.add_edge(self.gotos[label], self.labels[label], label="goto")
            except KeyError:
                warnings.warn("missing goto target. Skipping.", f"label={label}", f"gotos={self.gotos}")
        for n in self.returns:
            self.cfg.add_edge(n, exit_id, label="return")
        self.fringe.append(exit_id)

    def visit_default(self, n, **kwargs):
        self.visit_children(n)

    """STRAIGHT LINE STATEMENTS"""

    def enter_statement(self, n):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.fringe.append(node_id)

    def visit_expression_statement(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    def visit_declaration(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    """STRUCTURED CONTROL FLOW"""

    def visit_if_statement(self, n, **kwargs):
        children = self.get_named_children(n)
        condition = self.get_named_children(children[0])[0]
        condition_id = self.add_cfg_node(condition)
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append((condition_id, True))

        compound_statement = children[1]
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"

        if len(children) > 2:
            else_compound_statement = children[2]
            old_fringe = self.fringe
            self.fringe = [(condition_id, False)]
            self.visit(else_compound_statement)
            self.fringe = old_fringe + self.fringe
        else:
            self.fringe.append((condition_id, False))

    def visit_for_statement(self, n, **kwargs):
        # get metadata
        children = self.get_children(n)
        children = [c for c in children if self.get_type(c) != "comment"]
        child_types = [self.get_type(c) for c in children]
        i = 0
        while self.get_type(children[i]) != "(":
            i += 1
        i += 1
        if self.get_type(children[i]) == "declaration":
            has_init = True
            i += 1
        elif self.get_type(children[i]) == ";":
            has_init = False
            i += 1
        else:
            assert self.get_type(children[i]).endswith("_expression") or self.get_type(children[i]) in ("number_literal", "identifier"), (children[i], self.get_type(children[i]))
            has_init = True
            i += 1
            assert self.get_type(children[i]) == ";"
            i += 1
        # pointing after semicolon
        if self.get_type(children[i]) == ";":
            has_cond = False
        else:
            # assert_boolean_expression(children[i])
            has_cond = True
            i += 1
        # pointing at semicolon
        assert self.get_type(children[i]) == ";", (children[i], child_types, children[i].text.decode())
        i += 1
        if self.get_type(children[i]) == ")":
            has_incr = False
        else:
            assert self.get_type(children[i]).endswith("_expression") or self.get_type(children[i]) in ("number_literal", "identifier"), (children[i], child_types)
            has_incr = True

        named_children = self.get_named_children(n)
        i = 0
        if has_init:
            init = named_children[i]
            i += 1
        else:
            init = None
        if has_cond:
            cond = named_children[i]
            i += 1
        else:
            cond = None
        if has_incr:
            incr = named_children[i]
            i += 1
        else:
            incr = None

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
        self.fringe.append((cond_id, True))

        compound_statement = named_children[i]
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        if incr is not None:
            incr_id = self.add_cfg_node(incr)
            self.add_edge_from_fringe_to(incr_id)
            self.cfg.add_edge(incr_id, cond_id)
            self.cfg.add_edges_from(
                zip(self.continue_fringe, [incr_id] * len(self.continue_fringe)),
                label="continue",
            )
            self.continue_fringe = []
        else:
            self.add_edge_from_fringe_to(cond_id)
            self.cfg.add_edges_from(
                zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)),
                label="continue",
            )
            self.continue_fringe = []
        self.fringe.append((cond_id, False))

        self.fringe += [(n, "break") for n in self.break_fringe]
        self.break_fringe = []

    def visit_while_statement(self, n, **kwargs):
        named_children = self.get_named_children(n)
        cond = self.get_named_children(named_children[0])[0]
        cond_id = self.add_cfg_node(cond)

        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append((cond_id, True))

        compound_statement = named_children[1]
        self.visit(compound_statement)
        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append((cond_id, False))

        self.cfg.add_edges_from(
            zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)),
            label="continue",
        )
        self.continue_fringe = []
        self.fringe += [(n, "break") for n in self.break_fringe]
        self.break_fringe = []

    def visit_do_statement(self, n, **kwargs):
        dummy_id = self.add_dummy_node()
        self.add_edge_from_fringe_to(dummy_id)
        self.fringe.append(dummy_id)

        named_children = self.get_named_children(n)
        compound_statement = named_children[0]
        self.visit(compound_statement)

        cond = self.get_named_children(named_children[1])[0]
        cond_id = self.add_cfg_node(cond)
        self.add_edge_from_fringe_to(cond_id)
        self.cfg.add_edge(cond_id, dummy_id, label=str(True))
        self.fringe.append((cond_id, False))

        self.cfg.add_edges_from(
            zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)),
            label="continue",
        )
        self.continue_fringe = []
        self.fringe += [(n, "break") for n in self.break_fringe]
        self.break_fringe = []

    def visit_switch_statement(self, n, **kwargs):
        children = self.get_named_children(n)
        cond = self.get_named_children(children[0])[0]
        cond_id = self.add_cfg_node(cond)
        self.add_edge_from_fringe_to(cond_id)
        cases = self.get_named_children(children[1])
        default_was_hit = False
        for case in cases:
            while self.get_type(case) != "case_statement":
                if self.get_type(case) == "labeled_statement":
                    self.add_label_node(case)
                    case = self.get_named_children(case)
                else:
                    raise NotImplementedError(self.get_type(case))
            
            case_children = self.get_children(case)
            label_end = 0
            while self.get_type(case_children[label_end]) != ":":
                label_end += 1
            label_end -= 1
            body_begin = label_end + 2
            is_default = any(c for c in case_children if self.get_text(c) == "default")

            if len(self.get_children(case)) == 0:
                continue
            body_nodes = [
                c
                for c in case_children
                if body_begin <= self.get_attr(c, "idx")
            ]
            if is_default:
                default_was_hit = True
            case_text = self.get_text(case)
            case_text = case_text[: case_text.find(":") + 1]
            # TODO: append previous cases with no body
            self.fringe.append((cond_id, case_text))
            for body_node in body_nodes:
                should_continue = self.visit(body_node)
                if should_continue == False:
                    break
        if not default_was_hit:
            self.fringe.append((cond_id, "default:"))
        self.fringe += [(n, "break") for n in self.break_fringe]
        self.break_fringe = []

    def visit_return_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.visit_default(n, **kwargs)
        # This is meant to skip adding subsequent statements to the CFG.
        # TODO: consider how to handle this with goto statements.
        self.returns.append(node_id)
        return False

    def visit_break_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.break_fringe.append(node_id)
        self.visit_default(n, **kwargs)
        return False

    def visit_continue_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.continue_fringe.append(node_id)
        self.visit_default(n, **kwargs)
        return False

    def visit_goto_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        statement_identifier = self.get_named_children(n)[0]
        assert self.get_type(statement_identifier) == "statement_identifier"
        self.gotos[self.get_text(statement_identifier)] = node_id
        self.visit_default(n, **kwargs)

    def add_label_node(self, n):
        code = self.get_text(n)
        code = code[:code.find(":")+1]
        node_id = self.add_cfg_node(n, text=code)
        self.add_edge_from_fringe_to(node_id)
        statement_identifier = self.get_named_children(n)[0]
        assert self.get_type(statement_identifier) == "statement_identifier"
        self.labels[self.get_text(statement_identifier)] = node_id
        self.fringe.append(node_id)

    def visit_labeled_statement(self, n, **kwargs):
        self.add_label_node(n)
        self.visit_default(n, **kwargs)

def make_cfg(ast):
    visitor = CFGVisitor(ast)
    visitor.visit(ast.graph["root_node"])
    cfg = visitor.cfg
    # Postprocessing

    # pass through dummy nodes
    nodes_to_remove = []
    for n, attr in cfg.nodes(data=True):
        if attr.get("dummy", False):
            preds = list(cfg.predecessors(n))
            succs = list(cfg.successors(n))
            # Forward label from edges incoming to dummy.
            for pred in preds:
                new_edge_label = list(cfg.adj[pred][n].values())[0].get(
                    "label", None
                )
                for succ in succs:
                    cfg.add_edge(pred, succ, label=new_edge_label)
            nodes_to_remove.append(n)
    cfg.remove_nodes_from(nodes_to_remove)

    return visitor.cfg

def test():
    code = """int a = 30;

struct foo {
    int z;
};

int main()
{
    int x = 0;
    for (int i = 0; i < 10; i ++) {
        x -= i;
    }
    x += 20;
    switch (x) {
        case 0:
            x += 30;
            break;
        case 1:
            x -= 1;
        case 2:
            x -= a;
            break;
        default:
            return -2;
    }
    while (x > 10) {
        x -= 5;
    }
    do {
        x -= 5;
    } while (x > 0);
    return x;
}

struct foo;
"""
    tree = c_parser.parse(bytes(code, "utf8"))

    fig, ax = plt.subplots(2)
    ast = make_ast(tree.root_node)
    pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog="dot")
    nx.draw(
        ast,
        pos=pos,
        labels={n: attr["label"] for n, attr in ast.nodes(data=True)},
        with_labels=True,
        ax=ax[0],
    )

    cfg = make_cfg(ast)
    pos = nx.drawing.nx_agraph.graphviz_layout(cfg, prog="dot")
    nx.draw(
        cfg,
        pos=pos,
        labels={n: attr["label"] for n, attr in cfg.nodes(data=True)},
        with_labels=True,
        ax=ax[1],
    )
    nx.draw_networkx_edge_labels(
        cfg,
        pos=pos,
        edge_labels={
            (u, v): attr.get("label", "") for (u, v, attr) in cfg.edges(data=True)
        },
        ax=ax[1],
    )
    plt.show()
