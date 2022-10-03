from tests.utils import draw_ast
from tree_climber.tree_sitter_utils import c_parser, get_ast

def test_get_ast():
    code = """int main() {
    int x = 0;
    x += 5;
    return x;
}
"""
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = get_ast(tree.root_node)
    print(ast)
    draw_ast(ast)
