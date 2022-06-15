# tree-sitter-cfg

Convert tree-sitter AST to CFG for C programs.
AST -> CFG algorithm is based on Joern, specifically [CfgCreator.scala](https://github.com/joernio/joern/blob/6df0bbe6afad7f9b04bf0d1877e9797a7cdddcc4/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/controlflow/cfgcreation/CfgCreator.scala).

# Try it out

Clone [https://github.com/tree-sitter/tree-sitter-c.git](https://github.com/tree-sitter/tree-sitter-c.git) in the project root.
Then run `python main.py tests/data/example.c --print_ast --draw_cfg`
