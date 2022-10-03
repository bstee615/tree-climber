import pytest
from tests.utils import draw_ast
from tree_climber.tree_sitter_utils import c_parser, make_ast

@pytest.mark.slow()
def test_get_ast():
    code = """int main() {
    int x = 0;
    x += 5;
    return x;
}
"""
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = make_ast(tree.root_node)
    print(ast)
    draw_ast(ast)
