from tree_sitter import Language, Parser
import os

from tree_climber.config import TREE_SITTER_LIB_PREFIX
from git import Repo
import networkx as nx

languages = ["c"]
language_dirs = []

for lang in languages:
    clone_dir = os.path.join(TREE_SITTER_LIB_PREFIX, "tree-sitter-c")
    if not os.path.exists(clone_dir):
        repo_url = f"https://github.com/tree-sitter/tree-sitter-{lang}.git"
        Repo.clone_from(repo_url, clone_dir)
    language_dirs.append(clone_dir)

lib_file = os.path.join(TREE_SITTER_LIB_PREFIX, "build/languages.so")
Language.build_library(
    # Store the library in the `build` directory
    lib_file,
    # Include one or more languages
    [os.path.join(TREE_SITTER_LIB_PREFIX, "tree-sitter-c"),],
)

C_LANGUAGE = Language(lib_file, "c")
c_parser = Parser()
c_parser.set_language(C_LANGUAGE)

KEEP_KEYS = ["text", "start_point", "start_byte", "end_point", "end_byte", "is_named", "has_error", "type",
# "prev_sibling", "prev_named_sibling",
]

def attr_to_label(node_type, code):
    lines = code.splitlines()
    if len(lines) > 0:
        code = lines[0]
        max_len = 27
        trimmed_code = code[:max_len]
        if len(lines) > 1 or len(code) > max_len:
            trimmed_code += "..."
    else:
        trimmed_code = code
    return node_type + "\n" + trimmed_code

def make_ast(root):
    ast = nx.DiGraph()
    
    node_id = 0
    ast_root = None
    q = [(root, None, 0)]
    while len(q) > 0:
        v, parent, child_idx = q.pop(0)

        # extract node attributes
        attr = {k: getattr(v, k) for k in KEEP_KEYS}
        attr["text"] = attr["text"].decode()
        attr["label"] = attr_to_label(attr["type"], attr["text"].replace(":", ';'))
        attr["idx"] = child_idx

        # put in graph
        ast.add_node(node_id, **attr)
        if parent is not None:
            ast.add_edge(parent, node_id)

        # mark AST root
        if ast_root is None:
            ast_root = node_id

        # traverse children
        for child_idx, u in enumerate(v.children):
            q.append((u, node_id, child_idx))
        node_id += 1
    ast.graph["root_node"] = ast_root

    return ast
