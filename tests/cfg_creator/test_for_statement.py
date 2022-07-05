from tests.utils import *
import networkx as nx

def test_for_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10; i ++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

    cond_node = get_node_by_code(cfg, "i < 10")
    x_0_node = get_node_by_code(cfg, "x = 0;")
    assert get_adj_label(cfg, cond_node, x_0_node) == "True"
    FUNC_EXIT_node = get_node_by_label(cfg, "FUNC_EXIT")
    assert get_adj_label(cfg, cond_node, FUNC_EXIT_node) == "False"

def test_for_nocompound():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10; i ++)
            x = 0;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinit():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; i < 10; i ++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nocond():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; ; i++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10;) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinitincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; i < 10;) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinitcond():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; ; i++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nocondincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; ; ) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nothing():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; ; ) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nested():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            for (int j = 0; j < 10; j ++) {
                x += j;
            }
            x -= i;
        }
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (12, 13)
    assert len(list(nx.simple_cycles(cfg))) == 2

def test_for_break_all_cases():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            if (x > 5) {
                x = 22;
                break;
            }
            x = 10;
            if (i < 5) {
                return -1;
            }
            x += 5;
            break;
        }
        x = 11;
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (16, 18)
    assert nx.is_directed_acyclic_graph(cfg)
    
    cond_node = get_node_by_code(cfg, "i < 10")
    x_5_node = get_node_by_code(cfg, "x > 5")
    assert get_adj_label(cfg, cond_node, x_5_node) == "True"

    x_22_node = get_node_by_code(cfg, "x = 22;")
    assert get_adj_label(cfg, x_5_node, x_22_node) == "True"

    break_1_node, break_2_node = get_node_by_code(cfg, "break;", get="all")
    return_x_node = get_node_by_code(cfg, "return x;")
    x_11_node = get_node_by_code(cfg, "x = 11;")
    assert get_adj_label(cfg, break_1_node, x_11_node) == "break"
    assert (break_1_node, return_x_node) not in cfg.edges
    assert (break_1_node, cond_node) not in cfg.edges
    assert get_adj_label(cfg, break_2_node, x_11_node) == "break"
    assert (break_2_node, return_x_node) not in cfg.edges
    assert (break_2_node, cond_node) not in cfg.edges

def test_for_break():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            if (x > 5) {
                x = 0;
                break;
            }
            x = 10;
            if (i < 5) {
                return -1;
            }
            x += 5;
        }
        x = 10;
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (15, 17)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_continue():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            if (x > 5) {
                x = 22;
                continue;
            }
            x = 10;
            if (i < 5) {
                continue;
            }
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (13, 15)
    assert len(list(nx.simple_cycles(cfg))) == 3
    
    cond_node = get_node_by_code(cfg, "i < 10")
    x_5_node = get_node_by_code(cfg, "x > 5")
    assert get_adj_label(cfg, cond_node, x_5_node) == "True"

    x_22_node = get_node_by_code(cfg, "x = 22;")
    assert get_adj_label(cfg, x_5_node, x_22_node) == "True"

    continue_1_node, continue_2_node = get_node_by_code(cfg, "continue;", get="all")
    incr_node = get_node_by_code(cfg, "i ++")
    assert get_adj_label(cfg, continue_1_node, incr_node) == "continue"
    assert get_adj_label(cfg, continue_2_node, incr_node) == "continue"
