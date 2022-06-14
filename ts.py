from tree_sitter import Language, Parser

Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # Include one or more languages
  [
    'tree-sitter-c',
  ]
)

C_LANGUAGE = Language('build/my-languages.so', 'c')
parser = Parser()
parser.set_language(C_LANGUAGE)
tree = parser.parse(bytes("""int main()
{
    return 0;
}
""", "utf8"))

ts = tree.root_node
print(ts)
function_def = ts.children[0]
print(function_def)
function_decl = function_def.children
print(function_decl)

class MyVisitor:
    def __init__(self):
        pass
    
    def visit(self, n, indentation_level=0):
        getattr(self, f"enter_{n.type}", self.enter_default)(n, indentation_level)
        for c in n.children:
            self.visit(c, indentation_level+1)
        getattr(self, f"exit_{n.type}", self.exit_default)(n, indentation_level)

    def enter_default(self, n, indentation_level):
        print("\t" * indentation_level, "enter", n)

    def exit_default(self, n, indentation_level):
        print("\t" * indentation_level, "exit", n)

    def enter_translation_unit(self, n, indentation_level):
        print("TU:", n)

MyVisitor().visit(tree.root_node)
