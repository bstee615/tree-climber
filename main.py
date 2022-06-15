from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
import matplotlib.pyplot as plt
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    parser.add_argument("--print_ast", action="store_true", help="print AST")
    parser.add_argument("--draw_cfg", action="store_true", help="draw CFG")
    args = parser.parse_args()

    with open(args.filename, "rb") as f:
        tree = c_parser.parse(f.read())
    
    if args.print_ast:
        v = BaseVisitor()
        v.visit(tree.root_node)

    if args.draw_cfg:
        v = CFGCreator()
        cfg = v.generate_cfg(tree.root_node)
        print(cfg)
        pos = nx.spring_layout(cfg, seed=0)
        nx.draw(cfg, pos=pos)
        nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)})
        plt.show()
