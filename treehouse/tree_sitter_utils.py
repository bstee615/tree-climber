from tree_sitter import Language, Parser
import os

from treehouse.config import TREE_SITTER_C_PREFIX

Language.build_library(
    # Store the library in the `build` directory
    "lib/build/my-languages.so",
    # Include one or more languages
    [os.path.join(TREE_SITTER_C_PREFIX, "tree-sitter-c"),],
)

C_LANGUAGE = Language("lib/build/my-languages.so", "c")
c_parser = Parser()
c_parser.set_language(C_LANGUAGE)
