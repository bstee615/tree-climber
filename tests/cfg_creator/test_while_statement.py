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
