from tree_sitter_languages import get_parser
from pyvis.network import Network
import networkx as nx
from .util import concretize_graph, concretize_node, truncate


class AstNode:
    def __init__(self, ast_node):
        self.ast_node = ast_node
    
    def __str__(self):
        return f"{type(self).__name__} ({self.ast_node.type}) {repr(truncate(self.ast_node.text.decode()))}"

    def __hash__(self):
        return self.ast_node.id

    def asdict(self):
        return {
            "ast_node": concretize_node(self.ast_node),
        }


class AstVisitor:
    def __init__(self):
        self.graph = nx.DiGraph()

    def visit(self, node):
        # if node.is_missing or node.is_error:
        #     raise Exception("Error parsing AST!")
        ast_node = AstNode(node)
        for child in node.children:
            child_node = self.visit(child)
            self.graph.add_edge(ast_node, child_node)
        return ast_node

def visualize_ast(ast, fpath):
    net = Network(directed=True)
    net.from_nx(concretize_graph(ast))
    net.show(fpath, notebook=False)


if __name__ == "__main__":
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

    visitor = AstVisitor()
    ast_root = visitor.visit(tree.root_node)
    visitor.visualize(ast_root)
