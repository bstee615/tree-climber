from tree_climber.tree_sitter_utils import c_parser


class BaseVisitor:
    """
    Extensible AST visitor.
    Traverses and prints all nodes recursively by default.
    """

    def visit(self, n, **kwargs):
        return getattr(self, f"visit_{n.type}", self.visit_default)(n=n, **kwargs)

    def visit_children(self, n, **kwargs):
        for i, c in enumerate(n.children):
            should_continue = self.visit(c, child_idx=i, **kwargs)
            if should_continue == False:
                break

    def visit_default(self, n, **kwargs):
        print("enter", n, "kwargs", kwargs)
        self.visit_children(n)
        print("exit", n)


def test_print_ast():
    with open("tests/data/do_while_continue.c", "rb") as f:
        tree = c_parser.parse(f.read())

    v = BaseVisitor()
    v.visit(tree.root_node)
