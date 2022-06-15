from tests.utils import *
import networkx as nx

def test_screwy_program():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            for (int j = 0; j < 10; j ++) {
                if (true) {
                    if (false) {
                        x += j;
                    }
                    else {
                        while (true) {
                            while (false) {
                                x = 0;
                            }
                            if (x < 10) {
                                x += 5;
                            }
                            else {
                                x -= 5;
                            }
                        }
                    }
                }
            }
            x -= i;
        }
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (20, 26)
    assert len(list(nx.simple_cycles(cfg))) == 7

