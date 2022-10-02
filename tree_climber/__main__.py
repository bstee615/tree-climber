import json
from pathlib import Path
import traceback
from tree_climber.ast_creator import ASTCreator
from tree_climber.cfg_creator import CFGCreator
from tree_climber.dataflow.def_use import make_duc
from tree_climber.export.cpg import make_cpg
from tree_climber.tree_sitter_utils import c_parser
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
import argparse
from networkx.drawing.nx_agraph import write_dot


def draw_cfg(cfg, entry=None):
    if cfg.number_of_nodes() > 1000 or cfg.number_of_edges() > 1000:
        print("fuck man I'm not drawing that!")
        return
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw(cfg, pos=pos)
    nx.draw_networkx_labels(
        cfg,
        pos=pos,
        labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)},
    )
    if entry is not None:
        plt.title(cfg.nodes[entry]["n"].text)
    plt.show()


def detect_bugs(cpg):
    # detect npd bug with reaching definition
    ast = nx.edge_subgraph(
        cpg,
        [
            (u, v, k)
            for u, v, k, attr in cpg.edges(data=True, keys=True)
            if attr["graph_type"] == "AST"
        ],
    )
    duc = nx.edge_subgraph(
        cpg,
        [
            (u, v, k)
            for u, v, k, attr in cpg.edges(data=True, keys=True)
            if attr["graph_type"] == "DUC"
        ],
    )
    null_assignment = [
        n
        for n, attr in cpg.nodes(data=True)
        if attr.get("node_type", "<NO TYPE>")
        in ("expression_statement", "init_declarator")
        and any(
            ast.nodes[m].get("node_type", "<NO TYPE>") == "null"
            for m in nx.descendants(ast, n)
        )
    ]
    for ass in null_assignment:
        for usage in duc.adj[ass]:
            usage_attr = cpg.nodes[usage]
            call_expr = next(
                (
                    ch
                    for ch in ast.adj[usage]
                    if cpg.nodes[ch]["node_type"] == "call_expression"
                ),
                None,
            )
            if call_expr is None:
                continue
            id_expr = next(
                ch
                for ch in ast.adj[call_expr]
                if cpg.nodes[ch]["node_type"] == "identifier"
            )
            id_expr_attr = cpg.nodes[id_expr]
            if id_expr_attr["code"] == "printf":
                print(
                    f"""possible npd of {next(attr["label"] for u, v, k, attr in duc.edges(data=True, keys=True) if u == ass and v == usage)} at line {id_expr_attr["start"][0]+1} column {id_expr_attr["start"][1]+1}: {usage_attr["code"]}"""
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    parser.add_argument(
        "--draw_ast", action="store_true", help="draw AST (Abstract Syntax Tree)"
    )
    parser.add_argument(
        "--write_ast", type=str, help="write AST (Abstract Syntax Tree) to DOT"
    )
    parser.add_argument(
        "--draw_cfg", action="store_true", help="draw CFG (Control-Flow Graph)"
    )
    parser.add_argument(
        "--write_cfg", type=str, help="write CFG (Control-Flow Graph) to DOT"
    )
    parser.add_argument(
        "--write_cfg_json", action="store_true", help="write CFG to file"
    )
    parser.add_argument(
        "--draw_duc", action="store_true", help="draw DUC (Def-Use Chain)"
    )
    parser.add_argument(
        "--draw_cpg", action="store_true", help="draw CPG (Code Property Graph)"
    )
    parser.add_argument(
        "--each_function",
        action="store_true",
        help="draw each function's CFG as a separate plot",
    )
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
                pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog="dot")
                nx.draw(
                    ast,
                    pos=pos,
                    labels={n: attr["label"] for n, attr in ast.nodes(data=True)},
                    with_labels=True,
                )
                plt.show()
            if args.write_ast is not None:
                write_dot(ast, args.write_ast)

            cfg = CFGCreator.make_cfg(ast)
            if args.draw_cfg:
                if args.each_function:
                    funcs = [
                        n
                        for n, attr in cfg.nodes(data=True)
                        if attr["label"] == "FUNC_ENTRY"
                    ]
                    for func_entry in funcs:
                        func_cfg = nx.subgraph(
                            cfg, nx.descendants(cfg, func_entry) | {func_entry}
                        )
                        draw_cfg(func_cfg, entry=func_entry)
                else:
                    draw_cfg(cfg)
            if args.write_cfg is not None:
                write_dot(cfg, args.write_cfg)
            if args.write_cfg_json:
                for n in cfg.nodes():
                    del cfg.nodes[n]["n"]
                with open(str(filename) + ".graph.json", "w") as of:
                    json.dump(json_graph.node_link_data(cfg, attrs=None), of, indent=2)
            print("successfully parsed", filename)

            duc = make_duc(cfg)
            if args.draw_duc:
                pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog="dot")
                nx.draw(
                    duc,
                    pos=pos,
                    labels={n: attr["label"] for n, attr in duc.nodes(data=True)},
                    with_labels=True,
                )
                nx.draw_networkx_edge_labels(
                    duc,
                    pos=pos,
                    edge_labels={
                        (u, v): attr.get("label", "")
                        for u, v, attr in duc.edges(data=True)
                    },
                )
                plt.show()

            cpg = make_cpg(ast, cfg, duc)
            if args.draw_cpg:
                pos = nx.nx_pydot.graphviz_layout(cpg, prog="dot")
                nx.draw(cpg, pos=pos)
                nx.draw_networkx_labels(
                    cpg,
                    pos=pos,
                    labels={
                        n: attr.get("label", "<NO LABEL>")
                        for n, attr in cpg.nodes(data=True)
                    },
                )
                for graph_type, color in {
                    "AST": "black",
                    "CFG": "blue",
                    "DUC": "red",
                }.items():
                    nx.draw_networkx_edges(
                        cpg,
                        pos=pos,
                        edge_color=color,
                        edgelist=[
                            (u, v)
                            for u, v, k, attr in cpg.edges(keys=True, data=True)
                            if attr["graph_type"] == graph_type
                        ],
                    )
                nx.draw_networkx_edge_labels(
                    cpg,
                    pos=pos,
                    edge_labels={
                        (u, v): attr.get("label", "")
                        for u, v, k, attr in cpg.edges(keys=True, data=True)
                    },
                )
                plt.show()

            detect_bugs(cpg)
        except Exception:
            print("could not parse", filename)
            traceback.print_exc()
            raise
