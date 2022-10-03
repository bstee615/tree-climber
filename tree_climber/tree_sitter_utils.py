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

def get_ast(root):
    ast = nx.DiGraph()
    
    node_id = 0
    parent = None
    q = [root]
    while len(q) > 0:
        v = q.pop(0)
        ast.add_node(node_id, **{k: getattr(v, k) for k in KEEP_KEYS})
        if parent is not None:
            ast.add_edge(parent, node_id)
        parent = node_id
        node_id += 1
        q.extend(v.children)
    print(ast)
