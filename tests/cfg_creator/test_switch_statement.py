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
        switch(x > 0) {
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
