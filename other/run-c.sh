clang                                   \
  -I ../tree-sitter/lib/include            \
  ts-example-c.c                    \
  ../tree-sitter-c/src/parser.c         \
  ../tree-sitter/libtree-sitter.a          \
  -o ts-example

./ts-example