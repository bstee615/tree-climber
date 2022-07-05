import json
from pathlib import Path
import traceback
from tree_sitter_cfg.ast_creator import ASTCreator
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
import argparse
import os

def draw_cfg(cfg, entry=None):
    if cfg.number_of_nodes() > 1000 or cfg.number_of_edges() > 1000:
        print("fuck man I'm not drawing that!")
        return
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw(cfg, pos=pos)
    nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)})
    if entry is not None:
        plt.title(cfg.nodes[entry]["n"].text)
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    parser.add_argument("--draw_ast", action="store_true", help="print AST")
    parser.add_argument("--cfg", action="store_true", help="create CFG")
    parser.add_argument("--draw_cfg", action="store_true", help="draw CFG")
    parser.add_argument("--each_function", action="store_true", help="draw each function's CFG as a separate plot")
    parser.add_argument("--file", action="store_true", help="write CFG to file")
    args = parser.parse_args()

    args.filename = Path(args.filename)
    if args.filename.is_dir():
        filenames = list(args.filename.rglob("*.c"))
    elif args.filename.is_file():
        filenames = [args.filename]
    else:
        raise FileNotFoundError(args.filename)
    print("parsing", len(filenames), "files", filenames[:5])
    for filename in filenames:
        try:
            with open(filename, "rb") as f:
                tree = c_parser.parse(f.read())
            
            ast = ASTCreator.make_ast(tree.root_node)
            if args.draw_ast:
                pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog='dot')
                nx.draw(ast, pos=pos, labels={n: attr["label"] for n, attr in ast.nodes(data=True)}, with_labels = True)
                plt.show()

            if args.cfg:
                cfg = CFGCreator.make_cfg(ast)
                if args.draw_cfg:
                    if args.each_function:
                        funcs = [n for n, attr in cfg.nodes(data=True) if attr["label"] == "FUNC_ENTRY"]
                        for func_entry in funcs:
                            func_cfg = nx.subgraph(cfg, nx.descendants(cfg, func_entry) | {func_entry})
                            draw_cfg(func_cfg, entry=func_entry)
                    else:
                        draw_cfg(cfg)
                if args.file:
                    for n in cfg.nodes():
                        del cfg.nodes[n]["n"]
                    with open(str(filename) + ".graph.json", "w") as of:
                        json.dump(json_graph.node_link_data(cfg, attrs=None), of, indent=2)
            print("successfully parsed", filename)
        except Exception:
            print("could not parse", filename)
            traceback.print_exc()
            raise
