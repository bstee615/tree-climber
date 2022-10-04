import json
from pathlib import Path
import traceback
from tree_climber.ast import make_ast
from tree_climber.cfg import make_cfg
from tree_climber.dataflow.def_use import make_duc
from tree_climber.export.cpg import make_cpg
import networkx as nx
from networkx.readwrite import json_graph
from tree_climber.drawing_utils import draw_ast, draw_cfg, draw_duc, draw_cpg
from tree_climber.bug_detection import detect_null_pointer_dereference
import argparse
from networkx.drawing.nx_agraph import write_dot


def process_file(filename, args):
    # TODO reenable selective processing
    # compute_ast = (
    #     args.draw_ast
    #     or args.draw_cfg
    #     or args.draw_duc
    #     or args.draw_cpg
    # )
    # compute_cfg = args.draw_cfg or args.draw_duc or args.draw_cpg
    # compute_duc = args.draw_duc or args.draw_cpg
    # compute_cpg = args.draw_cpg or args.detect_bugs
    compute_ast = True
    compute_cfg = True
    compute_duc = True
    compute_cpg = True

    try:
        if compute_ast:
            ast = make_ast(filename)
            if args.draw_ast:
                draw_ast(ast)

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
            print("successfully parsed", filename)

        if compute_duc:
            duc = make_duc(ast, cfg)
            if args.draw_duc:
                draw_duc(duc)

        if compute_cpg:
            cpg = make_cpg(ast, cfg, duc)

        if args.detect_bugs:
            detect_null_pointer_dereference(cpg)
    except Exception:
        print("could not parse", filename)
        print(traceback.format_exc())
        if not args.continue_on_error:
            raise

    return cpg


def subgraph(graph, edge_types):
    return graph.edge_subgraph(
        [
            (u, v, k)
            for u, v, k, attr in graph.edges(data=True, keys=True)
            if attr["graph_type"] in edge_types
        ]
    )

def get_method_reference(n, typ, ast):
    if typ == "call_expression":
        return n, next(ast.nodes[s]["text"] for s in ast.successors(n) if ast.nodes[s]["type"] == "identifier")
    elif typ == "function_declarator" and not any(
        ast.nodes[a]["type"] == "function_definition"
        for a in ast.predecessors(n)
    ):
        return n, next(ast.nodes[s]["text"] for s in ast.successors(n) if ast.nodes[s]["type"] == "identifier")

def get_method_definition(n, typ, ast):
    if typ == "function_definition":
        declarator = next(s for s in ast.successors(n) if ast.nodes[s]["type"] == "function_declarator")
        return n, next(ast.nodes[s]["text"] for s in ast.successors(declarator) if ast.nodes[s]["type"] == "identifier")

def stitch_cpg(cpgs):
    combined_cpg = None
    # merge into one big CPG
    stitch_order = cpgs
    running_offset = 0
    for i in range(len(stitch_order)):
        stitch_order[i] = nx.convert_node_labels_to_integers(
            stitch_order[i], first_label=running_offset
        )
        running_offset += stitch_order[i].number_of_nodes()
    combined_cpg = nx.compose_all(cpgs)

    combined_ast = subgraph(combined_cpg, {"AST"})

    method_refs = [
        get_method_reference(n, typ, combined_ast) for n, typ in combined_cpg.nodes(data="type")
    ]
    method_refs = [n for n in method_refs if n is not None]

    method_defs = [
        get_method_definition(n, typ, combined_ast) for n, typ in combined_cpg.nodes(data="type")
    ]
    method_defs = [n for n in method_defs if n is not None]

    call_graph_edges = []
    methodname_to_defnode = {methodname: n for n, methodname in method_defs}
    for methodnode, methodname in method_refs:
        if methodname in methodname_to_defnode:
            call_graph_edges.append((methodnode, methodname_to_defnode[methodname]))
        else:
            call_graph_edges.append((methodnode, methodname))  # TODO: handle it by adding a new well-defined placeholder node

    combined_cpg.add_edges_from(call_graph_edges, graph_type="CALL", color="purple")

    return combined_cpg


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
    cpgs = []
    for filename in filenames:
        file_cpg = process_file(filename, args)
        cpgs.append(file_cpg)
    combined_cpg = stitch_cpg(cpgs)
    if args.draw_cpg:
        draw_cpg(combined_cpg)
    else:
        cpg_json = nx.node_link_data(combined_cpg)
        if args.output is None:
            print(json.dumps(cpg_json, indent=2))
        else:
            with open(args.output, "w") as f:
                json.dump(cpg_json, f)


if __name__ == "__main__":
    main()
