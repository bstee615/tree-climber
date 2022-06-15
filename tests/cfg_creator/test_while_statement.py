from tests.utils import parse_and_create_cfg
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
