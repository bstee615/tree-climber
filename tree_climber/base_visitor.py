class BaseVisitor:
    """
    Extensible AST visitor.
    Traverses and prints all nodes recursively by default.
    """

    def visit(self, n, **kwargs):
        """Delegate to the appropriate visitor."""
        return getattr(self, f"visit_{n.type}", self.visit_default)(n=n, **kwargs)

    def visit_children(self, n, **kwargs):
        """Visit all children of a node, breaking if the visitor returns false."""
        for i, c in enumerate(n.children):
            should_continue = self.visit(c, child_idx=i, **kwargs)
            if should_continue == False:
                break

    def visit_default(self, n, **kwargs):
        """Default visitor for nodes which are not implemented."""
        print("enter", n, "kwargs", kwargs)
        self.visit_children(n)
        print("exit", n)
