from treehouse.ast_creator import ASTCreator
from treehouse.dataflow.def_use import make_duc
from treehouse.tree_sitter_utils import c_parser
from treehouse.cfg_creator import CFGCreator
from tests.utils import *

def test_get_def_use_chain():
    code = """int main()
    {
        int i = 0;
        int x = 0;
        end:
        x -= 3;
        for (; true; ) {
            x += 5;
            if (x < 0) {
                goto end;
            }
        }
        printf("%d %d\\n", x, i);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)

    init_x_node = get_node_by_code(duc, "x = 0")
    init_i_node = get_node_by_code(duc, "i = 0")
    true_node = get_node_by_code(duc, "true")
    x_minus_assign_3_node = get_node_by_code(duc, "x -= 3;")
    x_plus_assign_5_node = get_node_by_code(duc, "x += 5;")
    x_assign_10_node = get_node_by_code(duc, "x = 10;")
    printf_node = get_node_by_code(cfg, """printf("%d %d\\n", x, i);""")
    return_node = get_node_by_code(cfg, "return x;")
    assert len(list(duc.predecessors(init_x_node))) == 0  # first assignment to x
    assert len(list(duc.predecessors(true_node))) == 0
    assert set(duc.predecessors(printf_node)) == {x_plus_assign_5_node, x_minus_assign_3_node, init_i_node}  # printf can print x defined by "x = 0" or "x += 5"
    assert set(duc.predecessors(return_node)) == {x_assign_10_node}  # return is dominated by "x = 10"
    assert set(duc.predecessors(x_plus_assign_5_node)) == {x_plus_assign_5_node, x_minus_assign_3_node}  # += should take into account its predecessor x
    assert set(duc.predecessors(x_minus_assign_3_node)) == {x_plus_assign_5_node, init_x_node} # x -= 3 uses x += 5 (later statement) because of goto

    assert duc.edges[(x_plus_assign_5_node, x_plus_assign_5_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(x_minus_assign_3_node, x_plus_assign_5_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(x_minus_assign_3_node, printf_node)].get("label", "<NO LABEL>") == "x"
    assert duc.edges[(init_i_node, printf_node)].get("label", "<NO LABEL>") == "i"
    assert duc.edges[(x_plus_assign_5_node, printf_node)].get("label", "<NO LABEL>") == "x"
