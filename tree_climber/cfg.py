class CfgNode:
    def __init__(self, ast_node):
        self.parents = []
        self.children = []

        self.ast_node = ast_node
    
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        if isinstance(self.ast_node, str):
            return f"{type(self).__name__} ({self.ast_node})"
        else:
            return f"{type(self).__name__} ({self.ast_node.type}) {repr(self.ast_node.text.decode())}"

    def add_parent(self, parent):
        self.parents.append(parent)

    def add_child(self, child, annotation=None):
        parent = self
        annotation_str = annotation or ""
        # print(f"Add child {parent} -{annotation_str}> {child}")
        parent.children.append(child)
        child.add_parent(parent)

    @property
    def id(self):
        return id(self)

class CfgSubgraph(CfgNode):
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end
    
    def add_parent(self, parent):
        self.begin.parents.append(parent)
    
    def add_child(self, child, annotation=None):
        parent = self
        while isinstance(parent, CfgSubgraph):
            parent = parent.end
        
        if child in parent.children:
            assert parent in child.parents
            print("SKIPPING", parent, child)
            return

        # if isinstance(child, CfgSubgraph):
        #     # print("FOO")
        #     child = child.begin
        # elif isinstance(child, CfgNode):
        #     pass
        
        # print("Add child", self, child)
        
        assert type(parent) == CfgNode, type(parent)
        assert type(child) == CfgNode, type(child)

        parent.add_child(child)

    def __str__(self):
        return f"begin: {self.begin} - end: {self.end}"

def is_cfg_statement(ast_node):
    """Return true if this node is a CFG statement."""
    return ast_node.type.endswith("_statement") and not ast_node.type == "compound_statement"

class CfgVisitor:
    def __init__(self):
        self.return_statements = []
        self.break_statements = []
        self.continue_statements = []
        self.subgraphs = []
        self.passes = []

    def fork(self):
        visitor = CfgVisitor()
        visitor.return_statements = self.return_statements
        visitor.break_statements = self.break_statements
        visitor.continue_statements = self.continue_statements
        visitor.subgraphs = self.subgraphs
        visitor.passes = self.passes
        return visitor

    def visit(self, node):
        """
        Convert a single node as the root to a subgraph in the CFG.
        Return two nodes, one root and one "tail", lowest point in the CFG.
        For subgraphs which terminate in multiple nodes, point all to a "pass-through" node which will be post-processed.

        Compound statements:
        a -> b -> c ; return (a, c)

        If statements:
        cond -T-> a -> pass ; return (cond, pass)
            -F-> b -/
        
        Loops:
        init -> c....o....n....d -F-> pass ; return (init, pass)
                -T-> update -/
        """

        if node.type == "if_statement":
            condition = node.child_by_field_name("condition")
            condition_cfg = CfgNode(condition)

            true_branch = node.child_by_field_name("consequence")
            true_cfg = self.visit(true_branch)

            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)
            condition_cfg.add_child(true_cfg, annotation="true")

            false_branch = node.child_by_field_name("alternative")
            if false_branch:
                false_cfg = self.visit(false_branch)
                condition_cfg.add_child(false_cfg, annotation="false")
                false_cfg.add_child(pass_cfg)
            else:
                condition_cfg.add_child(pass_cfg, annotation="false")
            true_cfg.add_child(pass_cfg)

            cfg_node = CfgSubgraph(condition_cfg, pass_cfg)
        elif node.type == "for_statement":
            initializer = node.child_by_field_name("initializer")
            condition = node.child_by_field_name("condition")
            update = node.child_by_field_name("update")
            stmt = next(child for child in reversed(node.children) if child.is_named and child.type != "comment")

            init_cfg = CfgNode(initializer)
            cond_cfg = CfgNode(condition)
            fork = self.fork()
            fork.break_statements = []
            fork.continue_statements = []
            stmt_cfg = fork.visit(stmt)
            update_cfg = CfgNode(update)
            pass_cfg = CfgNode("pass")
            self.passes.append(pass_cfg)

            for break_cfg in fork.break_statements:
                for c in break_cfg.children:
                    c.parents.remove(break_cfg)
                break_cfg.children = []
                break_cfg.add_child(pass_cfg)
            for continue_cfg in fork.continue_statements:
                for c in continue_cfg.children:
                    c.parents.remove(continue_cfg)
                continue_cfg.children = []
                continue_cfg.add_child(update_cfg)

            init_cfg.add_child(cond_cfg)
            cond_cfg.add_child(stmt_cfg, annotation="true")
            stmt_cfg.add_child(update_cfg)
            update_cfg.add_child(cond_cfg)
            cond_cfg.add_child(pass_cfg, annotation="false")
            cfg_node = CfgSubgraph(init_cfg, pass_cfg)
        elif node.type == "function_definition":
            entry_cfg = CfgNode("entry")
            body = node.child_by_field_name("body")
            fork = self.fork()
            fork.return_statements = []
            body_cfg = fork.visit(body)
            exit_cfg = CfgNode("exit")

            for return_cfg in fork.return_statements:
                for c in return_cfg.children:
                    c.parents.remove(return_cfg)
                return_cfg.children = []
                return_cfg.add_child(exit_cfg)

            entry_cfg.add_child(body_cfg)
            body_cfg.add_child(exit_cfg)
            cfg_node = CfgSubgraph(entry_cfg, exit_cfg)
        elif node.type in ("translation_unit", "compound_statement"):
            children = [child for child in node.children if child.is_named and not child.type == "comment"]
            cfg_nodes = []
            for child in children:
                cfg_node = self.visit(child)
                if len(cfg_nodes) > 0:
                    cfg_nodes[-1].add_child(cfg_node)
                cfg_nodes.append(cfg_node)
            if len(cfg_nodes) == 1:
                cfg_node = cfg_nodes[0]
            else:
                cfg_node = CfgSubgraph(cfg_nodes[0], cfg_nodes[-1])
        elif is_cfg_statement(node):
            cfg_node = CfgNode(node)
        else:
            raise NotImplementedError(f"({node.type}) {node.text.decode()}")
        
        if node.type == "break_statement":
            self.break_statements.append(cfg_node)
        if node.type == "continue_statement":
            self.continue_statements.append(cfg_node)
        if node.type == "return_statement":
            self.return_statements.append(cfg_node)
        if isinstance(cfg_node, CfgSubgraph):
            self.subgraphs.append(cfg_node)
        
        return cfg_node

if __name__ == "__main__":
    from tree_sitter_languages import get_parser
    parser = get_parser("c")
    tree = parser.parse(b"""int main() {
    x = 0;
    if (x > 0) {
        x += 15;
        return x;
    }
    else
        for (int i = 0; i < 10; i ++) {
            x += i;
            if (x)
                continue;
            x -= i;
        }
    return x + 10
}""")

    visitor = CfgVisitor()
    cfg = visitor.visit(tree.root_node)
    
    # normalize cfg
    for n in visitor.subgraphs:
        begin = n.begin
        while isinstance(begin, CfgSubgraph):
            begin = begin.begin
        parents = begin.parents
        for p in parents:
            p.children = [begin if id(c) == id(n) else c for c in p.children]
            
        end = n.end
        while isinstance(end, CfgSubgraph):
            end = end.end
        children = end.children
        for c in children:
            c.parents = [end if id(p) == id(n) else p for p in c.parents]

    for n in visitor.passes:
        parents = n.parents
        children = n.children
        for p in parents:
            p.children.remove(n)
            # print("CHILDREN", p.children, children)
            p.children.extend(children)
        for c in children:
            c.parents.remove(n)
            c.parents.extend(parents)

    from pyvis.network import Network

    net = Network(directed=True)
    visited = set()
    def dfs(n):
        # if n.id in visited:
        #     return
        print("Graph-izing", n, n.children)
        net.add_node(n.id, label=str(n))
        # for p in n.parents:
        #     net.add_node(p.id, label=str(p))
            # TODO: add annotation; net.add_edge(p.id, n.id, label=str() or "")
            # net.add_edge(p.id, n.id)
            # if "exit" in str(n):
            #     print(p, "->", "n")
        for child in n.children:
            net.add_node(child.id, label=str(child))
            net.add_edge(n.id, child.id)
            if "exit" in str(child):
                print(n, "->", child)
            if child.id not in visited:
                visited.add(child.id)
                dfs(child)
    dfs(cfg.begin)
    # print(net)
    net.show("mygraph.html", notebook=False)
