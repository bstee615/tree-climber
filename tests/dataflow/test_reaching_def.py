from tests.utils import *
from tree_sitter_cfg.dataflow.reaching_def import ReachingDefinitionSolver

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
    v = CFGCreator()
    cfg = v.generate_cfg(tree.root_node)
    solver = ReachingDefinitionSolver(cfg, verbose=1)
    solution = solver.solve()
    print(solution)
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "return" in attr["label"])] == {2}
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "printf" in attr["label"])] == {0, 1}
    draw(cfg, {n: sorted(set(map(solver.def2code.__getitem__, b))) for n, b in solution.items()})
