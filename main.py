import json
from pathlib import Path
import traceback
from treehouse.ast_creator import ASTCreator
from treehouse.cfg_creator import CFGCreator
from treehouse.dataflow.def_use import make_duc
from treehouse.tree_sitter_utils import c_parser
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
    parser.add_argument("--draw_ast", action="store_true", help="draw AST (Abstract Syntax Tree)")
    parser.add_argument("--draw_cfg", action="store_true", help="draw CFG (Control-Flow Graph)")
    parser.add_argument("--draw_duc", action="store_true", help="draw DUC (Def-Use Chain)")
    parser.add_argument("--each_function", action="store_true", help="draw each function's CFG as a separate plot")
    parser.add_argument("--write_cfg", action="store_true", help="write CFG to file")
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

            cfg = CFGCreator.make_cfg(ast)
            if args.draw_cfg:
                if args.each_function:
                    funcs = [n for n, attr in cfg.nodes(data=True) if attr["label"] == "FUNC_ENTRY"]
                    for func_entry in funcs:
                        func_cfg = nx.subgraph(cfg, nx.descendants(cfg, func_entry) | {func_entry})
                        draw_cfg(func_cfg, entry=func_entry)
                else:
                    draw_cfg(cfg)
            if args.write_cfg:
                for n in cfg.nodes():
                    del cfg.nodes[n]["n"]
                with open(str(filename) + ".graph.json", "w") as of:
                    json.dump(json_graph.node_link_data(cfg, attrs=None), of, indent=2)
            print("successfully parsed", filename)

            if args.draw_duc:
                duc = make_duc(cfg)
                pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog='dot')
                nx.draw(duc, pos=pos, labels={n: attr["label"] for n, attr in duc.nodes(data=True)}, with_labels = True)
                nx.draw_networkx_edge_labels(duc, pos=pos, edge_labels={(u, v): attr.get("label", "") for u, v, attr in duc.edges(data=True)})
                plt.show()
        except Exception:
            print("could not parse", filename)
            traceback.print_exc()
            raise
