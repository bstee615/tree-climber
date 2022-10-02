from turtle import clone
from tree_sitter import Language, Parser
import os

from tree_climber.config import TREE_SITTER_LIB_PREFIX
from git import Repo

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
