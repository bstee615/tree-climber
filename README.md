# tree-sitter-cfg

Convert tree-sitter AST to CFG for C programs.
AST -> CFG algorithm is based on Joern, specifically [CfgCreator.scala](https://github.com/joernio/joern/blob/6df0bbe6afad7f9b04bf0d1877e9797a7cdddcc4/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/controlflow/cfgcreation/CfgCreator.scala).

# Try it out

Clone [https://github.com/tree-sitter/tree-sitter-c.git](https://github.com/tree-sitter/tree-sitter-c.git) in the project root.
Then run `python main.py tests/data/example.c --print_ast --cfg --draw`

# Stress test

File [parse.sh](./tests/vs-joern/parse.sh) runs Joern and tree-sitter side by side to compare performance.
Use [joern-install.sh](./tests/vs-joern/joern-install.sh) to install Joern first.

Output 2022-06-15 19:44, v1.1.891 of Joern:
```
(tree-sitter-py38) benjis@AM:~/code/ts$ bash tests/vs-joern/parse.sh --joern tests/data/10000.c
executing /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala with params=Map(filename -> tests/data/10000.c)
Compiling /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala
creating workspace directory: /home/benjis/code/ts/workspace
Creating project `10000.c` for code at `tests/data/10000.c`
moving cpg.bin.zip to cpg.bin because it is already a database file
Creating working copy of CPG to be safe
Loading base CPG from: /home/benjis/code/ts/workspace/10000.c/cpg.bin.tmp
Code successfully imported. You can now query it using `cpg`.
For an overview of all imported code, type `workspace`.
Adding default overlays to base CPG
The graph has been modified. You may want to use the `save` command to persist changes to disk.  All changes will also be saved collectively on exit
script finished successfully
Some(())

real    0m14.143s
user    0m44.302s
sys     0m1.260s
(tree-sitter-py38) benjis@AM:~/code/ts$ bash tests/vs-joern/parse.sh --tree-sitter tests/data/10000.c

real    0m1.503s
user    0m1.385s
sys     0m0.111s
```
