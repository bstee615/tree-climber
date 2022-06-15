from tree_sitter import Language, Parser

class BaseVisitor:
    """
    Extensible AST visitor.
    Traverses and prints all nodes recursively by default.
    """

    def visit(self, n, indentation_level=0, **kwargs):
        getattr(self, f"visit_{n.type}", self.visit_default)(n=n, indentation_level=indentation_level, **kwargs)
    
    def visit_children(self, n, indentation_level, **kwargs):
        for c in n.children:
            self.visit(c, indentation_level+1, parent=n, siblings=n.children)

    def visit_default(self, n, indentation_level, **kwargs):
        print("\t" * indentation_level, "enter", n)
        self.visit_children(n, indentation_level)
        print("\t" * indentation_level, "exit", n)
