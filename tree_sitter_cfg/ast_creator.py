from matplotlib import pyplot as plt
import networkx as nx

from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.tree_sitter_utils import c_parser

def assert_boolean_expression(n):
    assert n.type.endswith("_statement") or n.type.endswith("_expression") or n.type in ("true", "false", "identifier"), n.type
def assert_branch_target(n):
    assert n.type.endswith("_statement") or n.type.endswith("_expression") or n.type in ("else",), n.type

class ASTCreator(BaseVisitor):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self):
        super(ASTCreator).__init__()
        self.ast = nx.DiGraph()
        self.node_id = 0
    
    @staticmethod
    def make_ast(root_node):
        visitor = ASTCreator()
        visitor.visit(root_node, parent_id=None)
        return visitor.ast

    def visit_for_statement(self, n, **kwargs):
        children = n.children
        i = 0
        while children[i].type != "(":
            i += 1
        i += 1
        if children[i].type == "declaration":
            has_init = True
            i += 1
        elif children[i].type == ";":
            has_init = False
            i += 1
        else:
            assert children[i].type in ("assignment_expression", "comma_expression")
            has_init = True
            i += 1
            assert children[i].type == ";"
            i += 1
        # pointing after semicolon
        if children[i].type == ";":
            has_cond = False
        else:
            assert_boolean_expression(children[i])
            has_cond = True
            i += 1
        # pointing at semicolon
        assert children[i].type == ";"
        i += 1
        if children[i].type == ")":
            has_incr = False
        else:
            assert children[i].type in ("update_expression", "binary_expression", "call_expression")
            has_incr = True
        self.visit_default(n, has_init=has_init, has_cond=has_cond, has_incr=has_incr, **kwargs)

    def visit_default(self, n, parent_id, **kwargs):
        code = n.text.decode()
        my_id = self.node_id
        self.node_id += 1
        if parent_id is None:
            self.ast.graph["root_node"] = my_id
        if n.is_named:
            def attr_to_label(node_type, code):
                lines = code.splitlines()
                code = lines[0]
                max_len = 27
                trimmed_code = code[:max_len]
                if len(lines) > 1 or len(code) > max_len:
                    trimmed_code += "..."
                return node_type + "\n" + trimmed_code
            self.ast.add_node(my_id, n=n, label=attr_to_label(n.type, code), code=code, node_type=n.type, start=n.start_point, end=n.end_point, **kwargs)
            if parent_id is not None:
                self.ast.add_edge(parent_id, my_id)
            self.visit_children(n, parent_id=my_id)

def test():
    code = """#include <stdio.h>
int main()
{
    int i = 0;
    for (; i < 10; i ++) {
        printf("%d\n", i);
    }
    return 0;
}
"""
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog='dot')
    nx.draw(ast, pos=pos, labels={n: attr["label"] for n, attr in ast.nodes(data=True)}, with_labels = True)
    plt.show()
