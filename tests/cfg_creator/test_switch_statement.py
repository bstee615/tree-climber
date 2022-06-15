from tests.utils import *
import networkx as nx

def test_if_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        switch(x > 0) {
            case 0:
                return 0;
            case 1:
                return 1;
            case 2:
                return 4;
            default:
                return -1;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (8, 10)
    assert nx.is_directed_acyclic_graph(cfg)
