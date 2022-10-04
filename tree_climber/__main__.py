import json
from pathlib import Path
import traceback
from tree_climber.ast import make_ast
from tree_climber.cfg import make_cfg
from tree_climber.dataflow.def_use import make_duc
from tree_climber.export.cpg import make_cpg
from tree_climber.tree_sitter_utils import c_parser
import networkx as nx
from networkx.readwrite import json_graph
from tree_climber.drawing_utils import draw_ast, draw_cfg, draw_duc, draw_cpg
from tree_climber.bug_detection import detect_null_pointer_dereference
import argparse
from networkx.drawing.nx_agraph import write_dot


def process_file(filename, args):
    compute_ast = (
        args.draw_ast
        or args.write_ast
        or args.draw_cfg
        or args.draw_duc
        or args.draw_cpg
    )
    compute_cfg = args.draw_cfg or args.draw_duc or args.draw_cpg
    compute_duc = args.draw_duc or args.draw_cpg
    compute_cpg = args.draw_cpg or args.detect_bug

    try:
        with open(filename, "rb") as f:
            tree = c_parser.parse(f.read())

        if compute_ast:
            ast = make_ast(tree.root_node)
            if args.draw_ast:
                draw_ast(ast)
            if args.write_ast is not None:
                write_dot(ast, args.write_ast)

        if compute_cfg:
            cfg = make_cfg(ast)
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

        if compute_duc:
            duc = make_duc(ast, cfg)
            if args.draw_duc:
                draw_duc(duc)

        if compute_cpg:
            cpg = make_cpg(ast, cfg, duc)
            if args.draw_cpg:
                draw_cpg(cpg)

        if args.detect_bugs:
            detect_null_pointer_dereference(cpg)
    except Exception:
        print("could not parse", filename)
        print(traceback.format_exc())
        if not args.continue_on_error:
            raise


def main():
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
        "--detect_bugs", action="store_true", help="detect bugs based on CPG"
    )
    parser.add_argument(
        "--each_function",
        action="store_true",
        help="draw each function's CFG as a separate plot",
    )
    parser.add_argument(
        "--continue_on_error",
        action="store_true",
        help="continue if a file errors out",
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
        process_file(filename, args)


if __name__ == "__main__":
    main()
