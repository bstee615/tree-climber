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
    """, draw_cfg=True)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 8)
    assert len(list(nx.simple_cycles(cfg))) == 3
