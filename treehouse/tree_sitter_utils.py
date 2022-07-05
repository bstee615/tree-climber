from tree_sitter import Language, Parser

Language.build_library(
    # Store the library in the `build` directory
    "build/my-languages.so",
    # Include one or more languages
    ["tree-sitter-c",],
)

C_LANGUAGE = Language("build/my-languages.so", "c")
c_parser = Parser()
c_parser.set_language(C_LANGUAGE)
