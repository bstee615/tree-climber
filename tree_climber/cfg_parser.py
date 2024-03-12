import warnings
from collections import defaultdict

import networkx as nx
from matplotlib import pyplot as plt

from tree_climber.ast_parser import ASTParser
from tree_climber.base_parser import BaseParser
from tree_climber.base_visitor import BaseVisitor
from tree_climber.util import Counter


class CFGParser(BaseVisitor, BaseParser):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self, ast):
        super(CFGParser).__init__()
        self.ast = ast
        self.cfg = nx.DiGraph()
        self.counter = Counter()
        self.fringe = []
        self.break_fringe = []
        self.continue_fringe = []
        self.gotos = {}
        self.labels = {}

    @staticmethod
    def parse(data):
        """
        Parse some data into a CFG.
        Can be some code, tree-sitter tree, or an AST.
        """
        if isinstance(data, nx.Graph):
            assert data.graph["graph_type"] == "AST"
            ast = data
        else:
            # TODO: Forward kwargs to ASTParser
            ast = ASTParser.parse(data)
        visitor = CFGParser(ast)
        visitor.visit(ast.graph["root_node"])
        visitor.postprocess()
        visitor.cfg.graph["graph_type"] = "CFG"
        # TODO: Make utilities on BaseParser to automatically inherit parent graph attributes
        visitor.cfg.graph["parents"] = {"AST": ast}
        return visitor.cfg

    def postprocess(self):
        """
        Perform final postprocessing steps on a CFG.
        """
        # pass through dummy nodes
        nodes_to_remove = []
        for n, attr in self.cfg.nodes(data=True):
            if attr.get("dummy", False):
                preds = list(self.cfg.predecessors(n))
                succs = list(self.cfg.successors(n))
                # Forward label from edges incoming to dummy.
                for pred in preds:
                    new_edge_label = list(self.cfg.adj[pred][n].values())[0].get(
                        "label", None
                    )
                    for succ in succs:
                        self.cfg.add_edge(pred, succ, label=new_edge_label)
                nodes_to_remove.append(n)
        self.cfg.remove_nodes_from(nodes_to_remove)

    def get_children(self, n):
        """Get AST children of a node."""
        return list(self.ast.successors(n))

    def visit(self, n, **kwargs):
        return getattr(
            self, "visit_" + self.ast.nodes[n]["node_type"], self.visit_default
        )(n=n, **kwargs)

    def visit_children(self, n, **kwargs):
        for c in self.ast.successors(n):
            should_continue = self.visit(c, **kwargs)
            if should_continue == False:
                break

    def add_dummy_node(self):
        """
        Add a dummy node to the CFG.
        Dummy nodes are nodes whose connections should be forwarded in a post-processing step.
        """
        node_id = self.counter.get_and_increment()
        self.cfg.add_node(node_id, dummy=True, label="DUMMY")
        return node_id

    def add_cfg_node(self, ast_node, label=None, **kwargs):
        """Add CFG node to the graph, inheriting properties from the progenitor AST node if any."""
        existing_kwargs = {}
        if ast_node is not None:
            attr = self.ast.nodes[ast_node]
            existing_kwargs.update(attr)
            existing_kwargs["ast_node"] = ast_node
        if label is not None:
            existing_kwargs["label"] = label
        existing_kwargs.update(kwargs)
        node_id = self.counter.get_and_increment()
        self.cfg.add_node(node_id, **existing_kwargs)
        return node_id

    def add_edge_from_fringe_to(self, dst_node_id):
        """
        Attach the current fringe to a node, transferring edge types if any are assigned.
        """
        fringe_by_type = defaultdict(list)
        for src_node_id in self.fringe:
            if isinstance(src_node_id, tuple):
                fringe_by_type[src_node_id[1]].append(src_node_id[0])
            else:
                fringe_by_type[None].append(src_node_id)
        for edge_type, fringe in fringe_by_type.items():
            kwargs = {}
            if edge_type is not None:
                kwargs["label"] = str(edge_type)
            self.cfg.add_edges_from(zip(fringe, [dst_node_id] * len(self.fringe)), **kwargs)
        self.fringe = []

    """
    VISITOR RULES
    """

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
        for n in nx.descendants(self.cfg, entry_id):
            attr = self.cfg.nodes[n]
            if attr.get("n", None) is not None and attr["n"].type == "return_statement":
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
        # TODO: Use child_by_field_name where possible
        condition = self.get_children(self.get_children(n)[0])[0]
        condition_id = self.add_cfg_node(condition)
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append((condition_id, True))

        compound_statement = self.get_children(n)[1]
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"

        if len(self.get_children(n)) > 2:
            else_compound_statement = self.get_children(n)[2]
            old_fringe = self.fringe
            self.fringe = [(condition_id, False)]
            self.visit(else_compound_statement)
            self.fringe = old_fringe + self.fringe
        else:
            self.fringe.append((condition_id, False))

    def visit_for_statement(self, n, **kwargs):
        n_attr = self.ast.nodes[n]
        # print(n, n_attr["node_type"], kwargs, n_attr)
        i = 0
        if n_attr.get("has_init", False):
            init = self.get_children(n)[i]
            i += 1
        else:
            init = None
        if n_attr.get("has_cond", False):
            cond = self.get_children(n)[i]
            i += 1
        else:
            cond = None
        if n_attr.get("has_incr", False):
            incr = self.get_children(n)[i]
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

        compound_statement = self.get_children(n)[i]
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
        cond = self.get_children(self.get_children(n)[0])[0]
        cond_id = self.add_cfg_node(cond)

        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append((cond_id, True))

        compound_statement = self.get_children(n)[1]
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

        compound_statement = self.get_children(n)[0]
        self.visit(compound_statement)

        cond = self.get_children(self.get_children(n)[1])[0]
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
        cond = self.get_children(self.get_children(n)[0])[0]
        cond_id = self.add_cfg_node(cond)
        self.add_edge_from_fringe_to(cond_id)
        cases = self.get_children(self.get_children(n)[1])
        default_was_hit = False
        for case in cases:
            while self.ast.nodes[case]["node_type"] != "case_statement":
                if self.ast.nodes[case]["node_type"] == "labeled_statement":
                    self.add_label_node(case)
                    case = self.get_children(case)[1]
                else:
                    raise NotImplementedError(self.ast.nodes[case]["node_type"])
            case_children = self.get_children(case)
            case_attr = self.ast.nodes[case]
            if len(self.get_children(case)) == 0:
                continue
            body_nodes = [
                c
                for c in case_children
                if case_attr["body_begin"] <= self.ast.nodes[c]["child_idx"]
            ]
            if case_attr["is_default"]:
                default_was_hit = True
            case_text = self.ast.nodes[case]["code"]
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
        statement_identifier_attr = self.ast.nodes[self.get_children(n)[0]]
        assert statement_identifier_attr["node_type"] == "statement_identifier"
        self.gotos[statement_identifier_attr["code"]] = node_id
        self.visit_default(n, **kwargs)

    def add_label_node(self, n):
        code = self.ast.nodes[n]["code"]
        code = code[:code.find(":")+1]
        node_id = self.add_cfg_node(n, code=code)
        self.add_edge_from_fringe_to(node_id)
        statement_identifier_attr = self.ast.nodes[self.get_children(n)[0]]
        assert statement_identifier_attr["node_type"] == "statement_identifier"
        self.labels[statement_identifier_attr["code"]] = node_id
        self.fringe.append(node_id)

    def visit_labeled_statement(self, n, **kwargs):
        self.add_label_node(n)
        self.visit_default(n, **kwargs)


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

    cfg = CFGParser.parse(code)

    fig, ax = plt.subplots(2)
    
    ast = cfg.graph["parents"]["AST"]
    pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog="dot")
    nx.draw(
        ast,
        pos=pos,
        labels={n: attr["label"] for n, attr in ast.nodes(data=True)},
        with_labels=True,
        ax=ax[0],
    )

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
