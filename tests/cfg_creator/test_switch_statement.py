from tests.utils import *
import networkx as nx

def test_switch_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        switch(true) {
            case 0:
                return 0;
            default:
                return 1;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert nx.is_directed_acyclic_graph(cfg)

def test_switch_complex():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        switch(x) {
            case 0:
                return 0;
            case 1:
                return 1;
            case 2:
                x ++;
            default:
                x = -1;
                break;
        }
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (10, 12)
    assert nx.is_directed_acyclic_graph(cfg)

    cond_node = get_node_by_code(cfg, "x")
    return_0_node = get_node_by_code(cfg, "return 0;")
    return_1_node = get_node_by_code(cfg, "return 1;")
    x_plus_node = get_node_by_code(cfg, "x ++;")
    x_minus_node = get_node_by_code(cfg, "x = -1;")
    break_node = get_node_by_code(cfg, "break;")
    return_x_node = get_node_by_code(cfg, "return x;")

    assert get_adj_label(cfg, cond_node, return_0_node) == "case 0:"
    assert get_adj_label(cfg, cond_node, return_1_node) == "case 1:"
    assert get_adj_label(cfg, cond_node, x_plus_node) == "case 2:"
    assert get_adj_label(cfg, cond_node, x_minus_node) == "default:"
    assert get_adj_label(cfg, break_node, return_x_node) == "break"

def test_switch_nodefault():
    cfg = parse_and_create_cfg("""int main()
    {
        switch(-1) {
            case 0:
                return 0;
            case 1:
                return 1;
        }
        return 5;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 7)
    assert nx.is_directed_acyclic_graph(cfg)

    cond_node = get_node_by_code(cfg, "-1")
    return_0_node = get_node_by_code(cfg, "return 0;")
    return_1_node = get_node_by_code(cfg, "return 1;")
    return_5_node = get_node_by_code(cfg, "return 5;")

    assert get_adj_label(cfg, cond_node, return_0_node) == "case 0:"
    assert get_adj_label(cfg, cond_node, return_1_node) == "case 1:"
    assert get_adj_label(cfg, cond_node, return_5_node) == "default:"
