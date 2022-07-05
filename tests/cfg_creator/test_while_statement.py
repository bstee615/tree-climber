from tests.utils import *
import networkx as nx

def test_while_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        while (true) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1

    true_node = get_node_by_code(cfg, "true")
    x_0_node = get_node_by_code(cfg, "x = 0;")
    assert get_adj_label(cfg, true_node, x_0_node) == "True"
    FUNC_EXIT_node = get_node_by_label(cfg, "FUNC_EXIT")
    assert get_adj_label(cfg, true_node, FUNC_EXIT_node) == "False"

def test_while_nested():
    cfg = parse_and_create_cfg("""int main()
    {
        while (true) {
            while (false) {
                x = 0;
            }
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 6)
    assert len(list(nx.simple_cycles(cfg))) == 2

def test_do_while_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        do {
            x = 0;
        }
        while (true);
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1
    
    true_node = get_node_by_code(cfg, "true")
    x_0_node = get_node_by_code(cfg, "x = 0;")
    assert get_adj_label(cfg, true_node, x_0_node) == "True"
    FUNC_EXIT_node = get_node_by_label(cfg, "FUNC_EXIT")
    assert get_adj_label(cfg, true_node, FUNC_EXIT_node) == "False"

def test_do_while_nested():
    cfg = parse_and_create_cfg("""int main()
    {
        do {
            while (x < 1) {
                do {
                    x = 0;
                }
                while (x < 2);
            }
        }
        while (x < 3);
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 8)
    assert len(list(nx.simple_cycles(cfg))) == 3
