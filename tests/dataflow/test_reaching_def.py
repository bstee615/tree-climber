from tests.utils import *
from treehouse.dataflow.reaching_def import ReachingDefinitionSolver

def test_solve():
    code = """int main()
    {
        int x = 0;
        if (true) {
            x += 5;
        }
        printf("%d\\n", x);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    solver = ReachingDefinitionSolver(cfg)
    solution_in, solution_out = solver.solve()
    assert solution_out[get_node_by_code(cfg, "return x;")] == {2}
    assert solution_out[get_node_by_code(cfg, """printf("%d\\n", x);""")] == {0, 1}
