from tree_sitter_cfg.tree_sitter_utils import c_parser

class BaseVisitor:
    """
    Extensible AST visitor.
    Traverses and prints all nodes recursively by default.
    """

    def visit(self, n, indentation_level=0, **kwargs):
        return getattr(self, f"visit_{n.type}", self.visit_default)(n=n, indentation_level=indentation_level, **kwargs)
    
    def visit_children(self, n, indentation_level, **kwargs):
        for c in n.children:
            should_continue = self.visit(c, indentation_level+1, parent=n, siblings=n.children)
            if should_continue == False:
                break

    def visit_default(self, n, indentation_level, **kwargs):
        print("\t" * indentation_level, "enter", n)
        self.visit_children(n, indentation_level)
        print("\t" * indentation_level, "exit", n)

def test_print_ast():
    with open("tests/data/do_while_continue.c", "rb") as f:
        tree = c_parser.parse(f.read())
    
    v = BaseVisitor()
    v.visit(tree.root_node)
