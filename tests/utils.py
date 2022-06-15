from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
import matplotlib.pyplot as plt

def parse_and_create_cfg(code):
    tree = c_parser.parse(bytes(code, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    return v.cfg

def draw(cfg, dataflow_solution=None):
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw(cfg, pos=pos, connectionstyle=f"arc3,rad=0.1")
    nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)})
    if dataflow_solution is not None:
        nx.draw_networkx_labels(cfg, pos=pos, font_color="r", labels={n: "\n\n\n{" + ", ".join(dataflow_solution[n]) + "}" if dataflow_solution[n] else "" for n in cfg.nodes()})
    plt.show()
