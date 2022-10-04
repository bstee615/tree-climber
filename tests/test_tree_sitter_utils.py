import pytest
from tests.utils import draw_ast
from tree_climber.utils import c_parser
from tree_climber.ast import make_ast_from_tree

@pytest.mark.slow()
def test_get_ast():
    code = """int main() {
    int x = 0;
    x += 5;
    return x;
}
"""
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = make_ast_from_tree(tree)
    print(ast)
    draw_ast(ast)
