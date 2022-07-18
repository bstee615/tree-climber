from tree_sitter import Language, Parser
import os

Language.build_library(
    # Store the library in the `build` directory
    "build/my-languages.so",
    # Include one or more languages
    [os.path.join(os.environ.get("treehouse__TREE_SITTER_C_PREFIX", "."), "tree-sitter-c"),],
)

C_LANGUAGE = Language("build/my-languages.so", "c")
c_parser = Parser()
c_parser.set_language(C_LANGUAGE)
