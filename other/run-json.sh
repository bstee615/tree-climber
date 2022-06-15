clang                                   \
  -I ../tree-sitter/lib/include            \
  ts-example-json.c                    \
  ../tree-sitter-json/src/parser.c         \
  ../tree-sitter/libtree-sitter.a          \
  -o ts-example

./ts-example