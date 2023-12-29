# tree-climber

Program analysis tools built on [tree-sitter](https://github.com/tree-sitter/tree-sitter).
Currently supports only C.

# Try it out

Install from pip:

```bash
pip install tree_climber
```

or run from source:

```bash
# install deps
pip install -r requirements.txt
# run on a test program
python -m tree_climber test.c
```

Feel free to open a PR with other platform-specific instructions.

See [developers.md](./developers.md) for developer setup instructions.

# Features

Examples shown on [test.c](./tests/data/example.c).

## Visualize AST

Visualize AST parsed by tree-sitter:

![AST example](./images/ast_example.png)

## Construct and visualize Control-flow graph (CFG)

Convert tree-sitter AST to CFG for C programs.
AST -> CFG algorithm is based on Joern, specifically [CfgCreator.scala](https://github.com/joernio/joern/blob/6df0bbe6afad7f9b04bf0d1877e9797a7cdddcc4/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/controlflow/cfgcreation/CfgCreator.scala).

![CFG example](./images/cfg_example.png)

## Monotonic dataflow analysis

See `dataflow_solver.py`.

## Construct and visualize Def-use chain (DUC)

![DUC example](./images/duc_example.png)

## Construct and visualize Code Property Graph (CPG)

CPG composes AST + CFG + DUC into one graph for combined analysis.
Eventual goal is feature parity with Joern's usage in ML4SE.

![CPG example](./images/cpg_example.png)

# Contribute

[Open issues on Github](https://github.com/bstee615/tree-climber/issues)
