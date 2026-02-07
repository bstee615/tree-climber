from tree_sitter import Language, Parser
from tree_sitter_languages import get_parser

# Initialize parser
parser = get_parser("cpp")

source_code = b"""void FUN1(STREAM VAR1) { uint32 VAR2; uint16 VAR3; uint16 VAR4; uint16 VAR5;  FUN2(VAR6, VAR7, "VAR8");   FUN3(VAR1, VAR4); FUN3(VAR1, VAR5);  if (VAR4 == VAR9) { switch (VAR5) { case VAR10: FUN4(VAR1); break;  case VAR11:  FUN5(VAR1, 2);        FUN6(VAR1, VAR3);       FUN7(VAR1, VAR12);        if (VAR3 < 0x000c) VAR12 = 0x815ed39d;       VAR13++;  #if VAR14  FUN8();    #endif  FUN9(); FUN10(); break;  case VAR15: FUN11(); break;  case VAR16: FUN12(VAR1, VAR2); FUN2(VAR6, VAR7, "VAR8", VAR2); break;  case VAR17: FUN13(); break;  default: FUN2(VAR6, VAR7, "VAR8", VAR5, VAR4); break;  } } else if (VAR4 == VAR18) { if (VAR5 == VAR19) FUN14(VAR1); } else FUN2(VAR6, VAR20, "VAR8", VAR4); }"""

tree = parser.parse(source_code)
root = tree.root_node

def print_tree(node, indent=0):
    print("  " * indent + f"{node.type} [{node.start_point}-{node.end_point}]")
    if node.type not in ["translation_unit", "ERROR", "compound_statement", "if_statement", "switch_statement"]:
        if indent < 8:  # Limit depth
            for child in node.children:
                print_tree(child, indent + 1)

print_tree(root)

# Check what's in the ERROR node
print("\n\n=== Analyzing ERROR node ===")
for child in root.children:
    print(f"Child type: {child.type}")
    if child.type == "ERROR":
        print("ERROR node children:")
        for error_child in child.children:
            print(f"  - {error_child.type}")
            if error_child.type != "function_definition":
                print(f"    Text: {error_child.text[:100]}")

