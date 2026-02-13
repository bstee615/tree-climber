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
    
    Also handles cases where a function definition is missing a return type.
    Also adds common type definitions to make normalized code parseable.
    Removes preprocessor directives that can break parsing.
    
    Args:
        code: The C++ function definition string
        
    Returns:
        The converted function definition string with necessary type definitions
    """
    # Strip leading/trailing whitespace
    code = code.strip()
    
    # Remove all preprocessor directives that break parsing
    # These need to be removed as they create malformed syntax when not properly closed
    code = re.sub(r'#if\s+\d+\s*', '', code)     # Remove #if 0 or #if 1
    code = re.sub(r'#ifdef\s+\w+\s*', '', code)  # Remove #ifdef MACRO
    code = re.sub(r'#ifndef\s+\w+\s*', '', code) # Remove #ifndef MACRO
    code = re.sub(r'#else\s*', '', code)         # Remove #else
    code = re.sub(r'#endif\s*', '', code)        # Remove #endif
    code = re.sub(r'#define\s+[^\n]*\n?', '', code)  # Remove #define statements
    
    # Fix malformed function calls with stray identifiers
    # Pattern: FUN() VAR, -> FUN(), (VAR is likely a macro that should be removed)
    code = re.sub(r'\)\s+(VAR\d+)\s*,', '), ', code)
    # Pattern: &VAR VAR27) -> &VAR) (removes trailing macro identifiers in argument lists)
    code = re.sub(r'(\w+)\s+(VAR\d+)\s*\)', r'\1)', code)
    
    # Remove standalone macro/variable identifiers that appear as statements
    # These are likely RETURN_FALSE, RETURN_MM_ERROR macros without proper syntax
    code = re.sub(r';\s*(VAR\d+)\s*;', '; ;', code)  # ; VAR31; -> ; ;
    code = re.sub(r'\{\s*(VAR\d+)\s*;', '{ ;', code)  # { VAR33; -> { ;
    code = re.sub(r'}\s*(VAR\d+)\s*;', '} ;', code)  # } VAR31; -> } ;
    
    # Remove double semicolons
    code = re.sub(r';\s*;', ';', code)
    
    # Declare variables that are used but not declared (from removed #if 0 blocks)
    # Insert declarations at the beginning of the function body
    # This is a simplified approach - just add common undeclared variables
    code = re.sub(r'(\{[^{]*?)(\s+if\s*\()', r'\1 int VAR35 = 0; void *VAR36 = NULL; void *VAR37 = NULL;\2', code, count=1)
    
    # Convert macro-based loop constructs to proper for loops
    # Pattern: FUN5(VAR13, ..., VAR16) { ... } -> for(int VAR16 = 0; VAR16 < 10; VAR16++) { ... }
    # This handles nla_for_each_nested and similar macros
    code = re.sub(r'(\w+)\s*\(\s*(\w+)\s*,\s*[^,)]+\s*,\s*(\w+)\s*\)\s*({[^}]*}|\S+;?)',
                  r'for(int \3 = 0; \3 < 10; \3++) \4', code)
    
    
    # Fix standalone macro identifiers that are likely macro calls  
    # Pattern: { VAR33; -> { ; (macro call after opening brace)
    code = re.sub(r'\{\s*(VAR\d+)\s*;', '{ ;', code)
    # Pattern: ; VAR31; -> ; ; (standalone macro calls between semicolons)
    code = re.sub(r';\s+(VAR\d+)\s*;', '; ;', code)
    # Pattern: } VAR31; -> } ; (standalone macro before closing brace)  
    code = re.sub(r'}\s+(VAR\d+)\s*;', '} ;', code)
    
    # Pattern 1: Match destructor - CLASS_NAME :: ~ FUNCTION_NAME ( ) { ... }
    pattern_destructor = r'^(\w+)\s*::\s*~\s*(\w+)\s*(.*)$'
    match_destructor = re.match(pattern_destructor, code, re.DOTALL)
    
    if match_destructor:
        # Extract function name and the rest (parameters and body)
        function_name = match_destructor.group(2)
        rest = match_destructor.group(3)
        # Add void return type for valid C syntax
        code = f"void {function_name} {rest}"
    else:
        # Pattern 2: Match member function - [return_type] CLASS_NAME :: FUNCTION_NAME ( ... ) [const] { ... }
        # This pattern captures: return type (one or more words), class name, function name, and rest
        pattern_member = r'^([\w\s]+?)\s+(\w+)\s*::\s*(\w+)\s*(.*)$'
        match_member = re.match(pattern_member, code, re.DOTALL)
        
        if match_member:
            return_type = match_member.group(1).strip()
            function_name = match_member.group(3)
            rest = match_member.group(4)
            # Remove 'const' qualifier if present after parameters
            rest = re.sub(r'\)\s+const\s+{', ') {', rest)
            # Reconstruct as a regular function
            code = f"{return_type} {function_name} {rest}"
    
    # Check if the code starts with a function name without return type
    # Pattern: FUNCTION_NAME ( ... ) { ... }
    pattern_no_return = r'^([A-Z_][A-Z0-9_]*)\s*\('
    match_no_return = re.match(pattern_no_return, code)
    
    if match_no_return:
        # Add void return type for valid C syntax
        code = f"void {code}"
    
    # Fix K&R-style or malformed function parameters (must be done AFTER adding return type)
    # Pattern: type FUN(VAR) -> type FUN(void *VAR)
    # This handles cases where parameter has no type specifier
    code = re.sub(r'(\w+)\s+(\w+)\s*\(\s*(\w+)\s*\)', r'\1 \2(void *\3)', code)
    
    # Add common type definitions for normalized code
    # These are placeholder types that appear in vulnerability datasets
    type_defs = """
        typedef void* STREAM;
        typedef unsigned int uint32;
        typedef unsigned short uint16;
        typedef unsigned char uint8;
    """
    return type_defs + code
source_code = """
public OSCommandInjection_good_scope_078(){
  byte inputBuffer[]=new byte[128];
  try {
    int byteCount=System.in.read(inputBuffer);
    if (byteCount <= 0) {
      return;
    }
    String command=new String(inputBuffer);
    command=command.substring(0,byteCount - 2);
    function(command);
  }
 catch (  IOException e) {
    final Logger logger=Logger.getAnonymousLogger();
    String exception="Exception " + e;
    logger.warning(exception);
  }
}
"""

# source_code = """
# VAR1 :: ~ FUN1 ( ) { { int VAR2 ; int VAR3 [ 10 ] = { 0 } ; if ( VAR4 >= 0 && VAR4 < ( 10 ) ) { VAR3 [ VAR4 ] = 1 ; for ( VAR2 = 0 ; VAR2 < 10 ; VAR2 ++ ) { FUN2 ( VAR3 [ VAR2 ] ) ; } } else { FUN3 ( "" ) ; } } } 
# """

def main():
    # new_source = convert_destructor_to_function(source_code)
    print(source_code)
    new_source = "public class Test { " + source_code + " }"
    cpg = analyze_source_code(source=new_source, language="java")
    data = cpg.save_json()
    new_cpg = CPG.load_json(data)
    with open("./output_cpg_new_java.json", "w", encoding="utf-8") as f:
        json.dump(new_cpg.to_dict(), f, indent=2)

if __name__ == "__main__":
    main()