import json
from pathlib import Path
import traceback
from tree_climber.ast import make_ast
from tree_climber.cfg import make_cfg
from tree_climber.dataflow.def_use import make_duc
from tree_climber.export.cpg import make_cpg, stitch_cpg
import networkx as nx
from tree_climber.utils import draw_ast, draw_cfg, draw_duc, draw_cpg
from tree_climber.bug_detection import detect_null_pointer_dereference
import argparse


def process_file(filename, args):
    """
    Process one file into a CPG.
    """
    try:
        ast = make_ast(filename)
        if args.draw_ast:
            draw_ast(ast)

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
        print("successfully parsed", filename)

        duc = make_duc(ast, cfg)
        if args.draw_duc:
            draw_duc(duc)

        cpg = make_cpg(ast, cfg, duc)

        if args.detect_bugs:
            detect_null_pointer_dereference(cpg)
    except Exception:
        print("could not parse", filename)
        print(traceback.format_exc())
        if not args.continue_on_error:
            raise

    return cpg


def output_cpg(cpg, args):
    """
    Write or draw CPG.
    """
    if args.draw_cpg:
        draw_cpg(cpg)
    else:
        cpg_json = nx.node_link_data(cpg)
        if args.output is None:
            print(json.dumps(cpg_json, indent=2))
        else:
            with open(args.output, "w") as f:
                json.dump(cpg_json, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    parser.add_argument(
        "--draw_ast", action="store_true", help="draw AST (Abstract Syntax Tree)"
    )
    parser.add_argument(
        "--draw_cfg", action="store_true", help="draw CFG (Control-Flow Graph)"
    )
    parser.add_argument(
        "--draw_duc", action="store_true", help="draw DUC (Def-Use Chain)"
    )
    parser.add_argument(
        "--draw_cpg", action="store_true", help="draw CPG (Code Property Graph)"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None, help="write CPG to file"
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

    filenames = get_files(args)

    cpgs = []
    for filename in filenames:
        file_cpg = process_file(filename, args)
        cpgs.append(file_cpg)
    combined_cpg = stitch_cpg(cpgs)

    output_cpg(combined_cpg, args)


def get_files(args):
    args.filename = Path(args.filename)
    if args.filename.is_dir():
        extensions = {".c", ".h"}
        filenames = [
            file for file in args.filename.iterdir() if file.suffix in extensions
        ]
    elif args.filename.is_file():
        filenames = [args.filename]
    else:
        raise FileNotFoundError(args.filename)
    print("parsing", len(filenames), "files", filenames[:5])
    return filenames


if __name__ == "__main__":
    main()
