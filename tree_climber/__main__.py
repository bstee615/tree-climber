import json
from pathlib import Path
from tree_climber.cpg import make_cpg
import networkx as nx
from tree_climber.utils import draw_cpg
from tree_climber.bug_detection import detect_null_pointer_dereference
import argparse


def main():
    args = get_args()
    filenames = get_files(args)
    combined_cpg = make_cpg(filenames, draw_ast=args.draw_ast, draw_cfg=args.draw_cfg, draw_duc=args.draw_duc)
    if args.detect_bugs:
        detect_null_pointer_dereference(combined_cpg)
    output_cpg(combined_cpg, args)


def get_args():
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
    return args


def get_files(args):
    """
    Get the list of files to process.
    """
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


if __name__ == "__main__":
    main()
