from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
import matplotlib.pyplot as plt

if __name__ == "__main__":
    tree = c_parser.parse(bytes("""int main()
    {
        int x = 0;
        x = x + 1;
        if (x > 1) {
            x += 5;
        }
        x = x + 2;
        for (int i = 0; i < 10; i ++) {
            x --;
        }
        x = x + 3;
        while (x < 0) {
            x ++;
            x = x + 1;
        }
        x = x + 4;
        return x;
    }
    """, "utf8"))
    
    v = BaseVisitor()
    v.visit(tree.root_node)

    v = CFGCreator()
    v.visit(tree.root_node)
    print(v.cfg)
    pos = nx.spring_layout(v.cfg, seed=0)
    nx.draw(v.cfg, pos=pos)
    nx.draw_networkx_labels(v.cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in v.cfg.nodes(data=True)})
    plt.show()
