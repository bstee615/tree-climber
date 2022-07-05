from tree_sitter_cfg.ast_creator import ASTCreator
from tree_sitter_cfg.dataflow.def_use import get_def_use_chain
from tree_sitter_cfg.tree_sitter_utils import c_parser
from tree_sitter_cfg.cfg_creator import CFGCreator
import matplotlib.pyplot as plt
import networkx as nx
from tests.utils import draw, get_node_by_code

def test_get_def_use_chain():
    code = """int main()
    {
        int i = 0;
        int x = 0;
        for (; true; ) {
            x += 5;
        }
        printf("%d %d\\n", x, i);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = get_def_use_chain(cfg)

    init_x_node = next(n for n, attr in duc.nodes(data=True) if "x = 0" in attr["label"])
    init_i_node = next(n for n, attr in duc.nodes(data=True) if "i = 0" in attr["label"])
    true_node = next(n for n, attr in duc.nodes(data=True) if "true" in attr["label"])
    x_plus_assign_5_node = next(n for n, attr in duc.nodes(data=True) if "x += 5" in attr["label"])
    x_assign_10_node = next(n for n, attr in duc.nodes(data=True) if "x = 10" in attr["label"])
    printf_node = get_node_by_code(cfg, """printf("%d %d\\n", x, i);""")
    return_node = get_node_by_code(cfg, "return x;")
    assert not any(set(duc.predecessors(init_x_node)))  # first assignment to x
    assert not any(set(duc.predecessors(true_node)))
    assert set(duc.predecessors(printf_node)) == {x_plus_assign_5_node, init_x_node, init_i_node}  # printf can print x defined by "x = 0" or "x += 5"
    assert set(duc.predecessors(return_node)) == {x_assign_10_node}  # return is dominated by "x = 10"
    assert set(duc.predecessors(x_plus_assign_5_node)) == {x_plus_assign_5_node, init_x_node}  # += should take into account its predecessor x

    assert duc.edges[(x_plus_assign_5_node, x_plus_assign_5_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(init_x_node, x_plus_assign_5_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(init_x_node, printf_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(init_i_node, printf_node)].get("label", "<NO LABEL>") == "i"
    assert duc.edges[(x_plus_assign_5_node, printf_node)].get("label", "<NO LABEL>") == "x"
