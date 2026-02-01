from tree_climber.classification.helper_parser import analyze_source_code
from tree_climber.cli.cpg import CPG
import json
import re
def convert_destructor_to_function(code: str) -> str:
    """
    Convert C++ destructor definition from format:
    'VAR1 :: ~ FUN1 ( ) { ... }'
    to simplified format:
    'void FUN1 ( ) { ... }' (for valid C syntax)
    or just 'FUN1 ( ) { ... }' if add_return_type=False
    
    Args:
        code: The C++ function definition string
        
    Returns:
        The converted function definition string
    """
    # Strip leading/trailing whitespace
    code = code.strip()
    
    # Pattern to match: CLASS_NAME :: ~ FUNCTION_NAME ( ) { ... }
    # We want to remove the CLASS_NAME :: ~ part
    pattern = r'^(\w+)\s*::\s*~\s*(\w+)\s*(.*)$'
    match = re.match(pattern, code, re.DOTALL)
    
    if match:
        # Extract function name and the rest (parameters and body)
        function_name = match.group(2)
        rest = match.group(3)
        # Add void return type for valid C syntax
        return f"void {function_name} {rest}"
    
    # If no match, return original code
    return code
source_code = """
void FUN1 ( ) { if ( FUN2 ( ) ) { FUN3 ( ( int ) '' ) ; } else { if ( FUN3 ( ( int ) '' ) == VAR1 ) { FUN4 ( "" ) ; } } } """

# source_code = """
# VAR1 :: ~ FUN1 ( ) { { int VAR2 ; int VAR3 [ 10 ] = { 0 } ; if ( VAR4 >= 0 && VAR4 < ( 10 ) ) { VAR3 [ VAR4 ] = 1 ; for ( VAR2 = 0 ; VAR2 < 10 ; VAR2 ++ ) { FUN2 ( VAR3 [ VAR2 ] ) ; } } else { FUN3 ( "" ) ; } } } 
# """

def main():
    new_source = convert_destructor_to_function(source_code)
    print(new_source)
    cpg = analyze_source_code(new_source, language="cpp")
    data = cpg.save_json()
    new_cpg = CPG.load_json(data)
    with open("./output_cpg_new_c.json", "w", encoding="utf-8") as f:
        json.dump(new_cpg.to_dict(), f, indent=2)

if __name__ == "__main__":
    main()