from matplotlib import pyplot as plt
import networkx as nx

from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.tree_sitter_utils import c_parser

class ASTCreator(BaseVisitor):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self):
        super(ASTCreator).__init__()
        self.ast = nx.DiGraph()
        self.node_id = 0
    
    def make_ast(self, root_node):
        self.visit(root_node, parent_id=None)

    def visit_default(self, n, parent_id):
        code = n.text.decode()
        my_id = self.node_id
        self.node_id += 1
        self.ast.add_node(my_id, n=n, label=code, code=code, node_type = n.type, start=n.start_point, end=n.end_point)
        if parent_id is not None:
            self.ast.add_edge(parent_id, my_id)
        self.visit_children(n, parent_id=my_id)

def test():
    code = """int main()
{
    return 0;
}
"""
    tree = c_parser.parse(bytes(code, "utf8"))
    ast_v = ASTCreator()
    ast_v.make_ast(tree.root_node)
    ast = ast_v.ast
    def attr_to_code(attr):
        lines = attr["code"].splitlines()
        code = lines[0]
        max_len = 27
        trimmed_code = code[:max_len]
        if len(lines) > 1 or len(code) > max_len:
            trimmed_code += "..."
        return attr["node_type"] + ": " + trimmed_code
    pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog='dot')
    nx.draw(ast, pos=pos, labels={n: attr_to_code(attr) for n, attr in ast.nodes(data=True)}, with_labels = True)
    plt.show()
